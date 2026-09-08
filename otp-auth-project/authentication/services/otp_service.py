

import hashlib
import hmac
import secrets
import redis
from django.conf import settings
from common.exceptions import APIException


def _get_redis_client():
  
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=int(settings.REDIS_PORT),
        db=0,
        decode_responses=True,
    )


class OTPService:
 

    def __init__(self):
        self.redis = _get_redis_client()

    def _otp_key(self, identifier_type, identifier):
        return f"otp:{identifier_type}:{identifier}"

    def _send_count_key(self, identifier_type, identifier):
        return f"otp:send_count:{identifier_type}:{identifier}"

    def _cooldown_key(self, identifier_type, identifier):
        return f"otp:cooldown:{identifier_type}:{identifier}"

    def _block_key(self, identifier_type, identifier):
        return f"otp:block:{identifier_type}:{identifier}"

    def _block_stage_key(self, identifier_type, identifier):
        return f"otp:block_stage:{identifier_type}:{identifier}"

    def _verify_attempts_key(self, identifier_type, identifier):
        return f"otp:verify_attempts:{identifier_type}:{identifier}"

  

    def _generate_otp(self):
        return f"{secrets.randbelow(10000):04d}"

    def _hash_otp(self, otp, identifier):
        message = f"{otp}:{identifier}".encode()
        return hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()
    def _check_not_blocked_or_cooling_down(self, identifier_type, identifier):
        block_key = self._block_key(identifier_type, identifier)
        ttl = self.redis.ttl(block_key)
        if ttl and ttl > 0:
            raise APIException(
                "Too many OTP requests. Please try again later.",
                status_code=429,
                errors={"retry_after": ttl},
            )

        cooldown_key = self._cooldown_key(identifier_type, identifier)
        ttl = self.redis.ttl(cooldown_key)
        if ttl and ttl > 0:
            raise APIException(
                "Please wait before requesting another OTP.",
                status_code=429,
                errors={"retry_after": ttl},
            )

    def _register_send_and_maybe_block(self, identifier_type, identifier):
    
        count_key = self._send_count_key(identifier_type, identifier)
        stage_key = self._block_stage_key(identifier_type, identifier)

        stage = int(self.redis.get(stage_key) or 0)

        new_count = self.redis.incr(count_key)
        if new_count == 1:
            if stage == 0:
                window_seconds = settings.OTP_FIRST_BLOCK_MINUTES * 60
            elif stage == 1:
                window_seconds = settings.OTP_SECOND_BLOCK_HOURS * 3600
            else:
                window_seconds = settings.OTP_LONG_BLOCK_HOURS * 3600
            self.redis.expire(count_key, window_seconds)

        if new_count >= settings.OTP_MAX_SENDS:
            if stage == 0:
                block_seconds = settings.OTP_FIRST_BLOCK_MINUTES * 60
                next_stage = 1
            elif stage == 1:
                block_seconds = settings.OTP_SECOND_BLOCK_HOURS * 3600
                next_stage = 2
            else:
               
                block_seconds = settings.OTP_LONG_BLOCK_HOURS * 3600
                next_stage = 2

            self.redis.set(self._block_key(identifier_type, identifier), "1", ex=block_seconds)
           
            self.redis.set(stage_key, next_stage, ex=30 * 24 * 3600)
            self.redis.delete(count_key)

    def generate_and_store(self, identifier_type, identifier):
        self._check_not_blocked_or_cooling_down(identifier_type, identifier)
        self._register_send_and_maybe_block(identifier_type, identifier)

        otp = self._generate_otp()
        hashed = self._hash_otp(otp, identifier)

        otp_key = self._otp_key(identifier_type, identifier)
        self.redis.set(otp_key, hashed, ex=settings.OTP_EXPIRY_SECONDS)

        # Fresh OTP means fresh attempt counter.
        self.redis.delete(self._verify_attempts_key(identifier_type, identifier))

        # Start the "please wait before resending" timer.
        self.redis.set(
            self._cooldown_key(identifier_type, identifier),
            "1",
            ex=settings.OTP_RESEND_COOLDOWN_SECONDS,
        )

        return otp

    def verify(self, identifier_type, identifier, otp_input):
        otp_key = self._otp_key(identifier_type, identifier)
        stored_hash = self.redis.get(otp_key)

        if not stored_hash:
            raise APIException(
                "OTP has expired or was not requested. Please request a new one.",
                status_code=400,
            )

        attempts_key = self._verify_attempts_key(identifier_type, identifier)
        attempts = int(self.redis.get(attempts_key) or 0)

        if attempts >= settings.OTP_MAX_VERIFY_ATTEMPTS:
           
            self.redis.delete(otp_key)
            self.redis.delete(attempts_key)
            raise APIException(
                "Too many incorrect attempts. Please request a new OTP.",
                status_code=400,
            )

        candidate_hash = self._hash_otp(otp_input, identifier)

       
        if not hmac.compare_digest(candidate_hash, stored_hash):
            new_attempts = self.redis.incr(attempts_key)
            if new_attempts == 1:
                # Let the attempt counter expire alongside the OTP itself.
                remaining_ttl = self.redis.ttl(otp_key)
                if remaining_ttl and remaining_ttl > 0:
                    self.redis.expire(attempts_key, remaining_ttl)
            raise APIException("Incorrect OTP. Please try again.", status_code=400)

      
        self.redis.delete(otp_key)
        self.redis.delete(attempts_key)
        self.redis.delete(self._cooldown_key(identifier_type, identifier))
        return True
