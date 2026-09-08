# OTP-Only Authentication API (Django + DRF)

A beginner-friendly backend that lets users register and log in using
**OTP only** — no passwords, ever, for normal users. Built with Django,
Django REST Framework, PostgreSQL, Redis, Docker, MSG91 (SMS OTP), and
SMTP (email OTP).

This README explains: how to run the project from zero, every API
endpoint, the database design, the Redis design, and the security
decisions behind the code. Read it alongside the comments in the code —
almost every function has a comment explaining **why** it exists, not
just what it does.

---

## 1. Project structure

```
otp-auth-project/
├── docker-compose.yml        # Runs Django + PostgreSQL + Redis together
├── Dockerfile                 # How to build the Django container
├── .dockerignore
├── .env                       # Your real secrets (never commit this)
├── .env.example                # Template for .env
├── .gitignore
├── requirements.txt
├── manage.py
│
├── config/                    # Django project settings
│   ├── settings.py            # Everything reads from .env - no hard-coded secrets
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── authentication/             # The only Django app in this project
│   ├── models.py               # Custom User model (mobile-first, no password)
│   ├── serializers.py          # Request validation for every endpoint
│   ├── views.py                 # One class per endpoint - thin, readable
│   ├── urls.py
│   ├── admin.py                 # Django Admin configuration
│   ├── services/
│   │   ├── otp_service.py       # The heart of the system - see section 6
│   │   ├── msg91_service.py     # Sends SMS OTPs
│   │   ├── email_service.py     # Sends email OTPs
│   │   └── jwt_service.py       # Wraps Simple JWT token creation
│   ├── templates/emails/
│   │   └── otp_email.html       # The HTML email OTP template
│   └── migrations/
│
└── common/                     # Small shared helpers used everywhere
    ├── exceptions.py            # Makes every error response the same shape
    ├── permissions.py
    └── utils.py                 # Response helpers + phone number normalization
```

Why this structure and not something fancier? Because there's genuinely
only one Django app in this project (`authentication`), so splitting it
into multiple apps would just add indirection without benefit. The
`services/` folder is the one deliberate extra layer — it exists because
OTP logic, SMS sending, and email sending are each reused by more than
one view, and because you told us you might swap SMS providers later.

---

## 2. Step-by-step setup (from zero)

### Step 1 — Install Docker
Install Docker Desktop (Mac/Windows) or Docker Engine + Docker Compose
(Linux) from https://docs.docker.com/get-docker/. Confirm it works:

```bash
docker --version
docker compose version
```

### Step 2 — Get the project onto your machine
Unzip the project (or `git clone` it if you've pushed it to a repo) and
`cd` into the folder:

```bash
cd otp-auth-project
```

### Step 3 — Create your `.env` file
Copy the example file and fill in real values:

```bash
cp .env.example .env
```

At minimum, for local development, set:
- `SECRET_KEY` — any long random string (Django needs this)
- `POSTGRES_PASSWORD` — any password, this is your local dev database
- `MSG91_AUTH_KEY`, `MSG91_TEMPLATE_ID`, `MSG91_SENDER_ID` — from your
  MSG91 dashboard (https://msg91.com) — required only if you actually
  want SMS OTPs to be delivered; the app still runs without them, it
  will just log a failed-send message instead of erroring out.
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — an SMTP account (e.g. a
  Gmail account with an "app password") — required only for real email
  delivery.

**Never commit your real `.env` file** — `.gitignore` already excludes it.

### Step 4 — Build and start everything

```bash
docker compose up --build
```

This starts three containers: `web` (Django), `db` (PostgreSQL), and
`redis` (Redis). The first time you run this it will take a minute to
download the base images.

### Step 5 — Run database migrations
In a second terminal (leave `docker compose up` running):

```bash
docker compose exec web python manage.py migrate
```

(A ready-made migration is already included in this project, so this
step just applies it — see section 3 below if you ever change
`models.py` and need to generate a new one.)

### Step 6 — Create an admin user
So you can log into the Django Admin panel:

```bash
docker compose exec web python manage.py createsuperuser
```

It will ask for `mobile_number`, `country_code`, `name`, and a
`password` — the password is ONLY used to log into `/admin/`, never the
API (see section 5, "Why superusers have a password but nobody else does").

### Step 7 — Try it out
- API base URL: `http://localhost:8000/api/auth/`
- Admin panel: `http://localhost:8000/admin/`

Try registering a user with `curl` or Postman:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Rahul", "country_code": "+91", "mobile": "9876543210"}'
```

### Step 8 — Stopping everything

```bash
docker compose down
```

Add `-v` (`docker compose down -v`) if you also want to wipe the
PostgreSQL data volume and start completely fresh next time.

### If you ever change `models.py`
Generate and apply a new migration:

```bash
docker compose exec web python manage.py makemigrations authentication
docker compose exec web python manage.py migrate
```

---

## 3. Authentication flows (how it all fits together)

### Registration (mobile only, no email needed yet)
```
Register (name + mobile)
   ↓
Backend creates an unverified user + generates OTP
   ↓
OTP sent via MSG91 SMS
   ↓
POST /verify-mobile-otp/  (first time = registration)
   ↓
Mobile marked verified, account fully active
```

### Mobile login (after registration)
```
POST /login/mobile/           -> sends a fresh OTP
   ↓
POST /verify-mobile-otp/      -> mobile ALREADY verified, so this
                                  completes a LOGIN instead and
                                  returns JWT access + refresh tokens
```

Notice that `/verify-mobile-otp/` is reused for both registration and
login. The view distinguishes between the two cases by checking whether
the user's `is_mobile_verified` flag was already `True` *before* this
verification: first time ever → registration completes (no tokens
yet, matching the spec's example response). Already verified before →
this is a login, so we generate JWT tokens. This avoids having two
near-identical endpoints just because they're triggered from different
places.

### Adding + verifying an email later
A user can register and use the app with just a mobile number — email
is never forced. Later, they can call:

```
POST /add-email/  (while logged in)
   ↓
OTP sent to the new email address
   ↓
POST /verify-email-otp/  -> email marked verified + tokens issued
```

### Email login (once an email has been added)
```
POST /login/email/            -> sends OTP to that email
   ↓
POST /verify-email-otp/       -> marks email verified (if this is the
                                  first time) and ALWAYS returns JWT
                                  tokens, since email is only ever used
                                  to log in, never to create an account
```

---

## 4. API Reference

All responses share one of these two shapes:

```json
// success
{ "success": true,  "message": "...", "data": {} }

// error
{ "success": false, "message": "...", "errors": {} }
```

HTTP status codes used:
| Code | Meaning in this project |
|------|--------------------------|
| 200  | Request succeeded (login, verification, fetch, refresh, logout) |
| 201  | A new resource was created (registration) |
| 400  | Validation failed, wrong/expired OTP, bad refresh token |
| 401  | Missing or invalid JWT access token |
| 403  | Authenticated but not allowed to do this (not used much here) |
| 404  | No account found for that mobile/email |
| 409  | Conflict — e.g. mobile/email already registered |
| 429  | Rate limited — too many OTP requests |
| 500  | Unexpected server error |

### `POST /api/auth/register/`
Auth required: No

Request:
```json
{ "name": "Rahul", "country_code": "+91", "mobile": "9876543210" }
```
Validation: name (2+ chars), valid country code, valid mobile number for
that country (using the `phonenumbers` library).

Success (201):
```json
{ "success": true, "message": "OTP sent successfully",
  "data": { "next_step": "verify_mobile_otp" } }
```
Errors: 400 invalid input, 409 mobile already registered & verified.

### `POST /api/auth/verify-mobile-otp/`
Auth required: No

Request:
```json
{ "mobile": "9876543210", "country_code": "+91", "otp": "1234" }
```
Success (200) — first time (registration):
```json
{ "success": true, "message": "Mobile number verified successfully", "data": {} }
```
Success (200) — already verified before (login):
```json
{ "success": true, "message": "Login successful",
  "data": { "access_token": "...", "refresh_token": "..." } }
```
Errors: 400 wrong/expired OTP or too many attempts, 404 unknown mobile.

### `POST /api/auth/resend-mobile-otp/`
Auth required: No. Request: `{ "mobile": "...", "country_code": "+91" }`.
Subject to the resend cooldown + block rules (see section 6).

### `POST /api/auth/login/mobile/`
Auth required: No. Request: `{ "mobile": "...", "country_code": "+91" }`.
Only works if the mobile number is already registered AND verified.
Success (200): same shape as registration's OTP-sent response. Follow
up with `POST /verify-mobile-otp/` to complete login.

### `POST /api/auth/login/email/`
Auth required: No. Request: `{ "email": "user@example.com" }`.
Success (200):
```json
{ "success": true, "message": "OTP sent to email",
  "data": { "next_step": "verify_email_otp" } }
```
Errors: 404 if no user has this email.

### `POST /api/auth/verify-email-otp/`
Auth required: No. Request: `{ "email": "...", "otp": "1234" }`.
Success (200):
```json
{ "success": true, "message": "Email verified successfully",
  "data": { "access_token": "...", "refresh_token": "..." } }
```

### `POST /api/auth/resend-email-otp/`
Auth required: No. Request: `{ "email": "..." }`.

### `POST /api/auth/add-email/`
Auth required: **Yes** (`Authorization: Bearer <access_token>`).
Request: `{ "email": "user@example.com" }`. Attaches an email to the
logged-in user and sends a verification OTP. Errors: 409 if the email
is already used by another account.

### `POST /api/auth/token/refresh/`
Auth required: No (the refresh token itself is the credential).
Request: `{ "refresh": "REFRESH_TOKEN" }`.
Success (200):
```json
{ "success": true, "message": "Token refreshed successfully",
  "data": { "access_token": "...", "refresh_token": "..." } }
```
Note: the old refresh token is blacklisted the moment it's used — see
section 5.

### `POST /api/auth/logout/`
Auth required: Yes. Request: `{ "refresh": "REFRESH_TOKEN" }`.
Blacklists the refresh token so it can never be used again.

### `GET /api/auth/me/`
Auth required: Yes. Returns the logged-in user's profile fields (see
`UserSerializer` in `serializers.py`).

---

## 5. JWT authentication — access + refresh tokens

**Why two tokens instead of one?**
- The **access token** is sent with every API request and is
  short-lived (15 minutes by default). If it's ever stolen (e.g. from
  browser storage or a log file), the damage window is small — it stops
  working on its own soon.
- The **refresh token** lives much longer (7 days by default) but is
  used rarely — only to fetch a new access token via
  `/api/auth/token/refresh/`. This is what lets a user stay "logged in"
  for a week without re-entering an OTP every 15 minutes.

**Refresh token rotation.** Every time `/token/refresh/` is called, the
old refresh token is blacklisted and a completely new access+refresh
pair is issued. This means a refresh token can only ever be used once —
if an attacker steals one and uses it, and the real user later tries to
use their (now-invalid) copy, that's a signal something is wrong. It
also limits how long a stolen refresh token stays useful.

**How logout actually works.** JWTs are stateless by design — the
server can't "delete" an access token early. What logout really does is
blacklist the refresh token, so no more access tokens can be minted
from that session. The existing access token will still technically
work until it naturally expires (at most `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`
after logout) — this is a normal, accepted trade-off of JWT-based auth
and is why access tokens are kept short-lived.

**Why do only superusers have a password?** Django's admin panel
(`/admin/`) is built around username+password login, and rewriting it
to use OTPs would be a lot of extra work for very little benefit — only
trusted staff use the admin panel, not end users. So: normal users get
`set_unusable_password()` (password login is impossible for them, by
design), while `createsuperuser` sets a real password used *only* to
access `/admin/`. The public API never accepts a password from anyone.

---

## 6. OTP + Redis design (the core of this project)

### Why Redis and not PostgreSQL for OTPs?
Every piece of data in this section is temporary by nature — an OTP
should vanish in 5 minutes, a cooldown should vanish in 60 seconds, a
block should vanish in 30 minutes/3 hours/etc. Redis lets us set an
exact **TTL (time-to-live)** on each key, so expired data disappears
automatically with zero cleanup code. Storing this in PostgreSQL would
mean either a cron job to delete expired rows, or timestamp comparisons
on every read — Redis does this for free.

### Why rate limiting matters so much for a 4-digit OTP
A 4-digit OTP has only **10,000 possible values** (0000–9999). Without
strict rate limiting, an attacker could realistically try all 10,000
combinations against a phone number in a short time and eventually
guess correctly. This is why this project enforces limits at **two
layers**:
1. How many *times* an OTP can be **sent** (prevents SMS/email spam
   and gives an attacker fewer "rounds" to attack).
2. How many *wrong guesses* are allowed per OTP before it's invalidated
   (`OTP_MAX_VERIFY_ATTEMPTS`, default 5) — this is the layer that
   actually stops brute-forcing, since 5 guesses out of 10,000 is a
   ~0.05% success chance per OTP lifetime.

### Redis keys used (all values below are configurable via `.env`)

| Key pattern | Purpose | TTL |
|---|---|---|
| `otp:mobile:<number>` / `otp:email:<email>` | The HMAC-hashed OTP (never plain text) | `OTP_EXPIRY_SECONDS` (default 300s / 5 min) |
| `otp:cooldown:mobile:<number>` | Blocks resending too fast | `OTP_RESEND_COOLDOWN_SECONDS` (default 60s) |
| `otp:send_count:mobile:<number>` | Counts sends within the current cycle | Matches the block length of the *next* stage |
| `otp:block:mobile:<number>` | Exists while the user is blocked from sending | 30 min → 3 hr → 24 hr (see below) |
| `otp:block_stage:mobile:<number>` | Remembers which block stage the user is in (0/1/2) so repeat abuse keeps escalating | 30 days |
| `otp:verify_attempts:mobile:<number>` | Counts wrong OTP guesses | Same TTL as the OTP itself |

(The `email:` versions use the exact same pattern with the email
address as the identifier.)

### The 3-strike escalating block, explained
```
3 OTP sends allowed
   ↓ (3rd one sent)
BLOCKED for OTP_FIRST_BLOCK_MINUTES (default 30 min)
   ↓ (block expires)
3 more OTP sends allowed
   ↓ (3rd one sent)
BLOCKED for OTP_SECOND_BLOCK_HOURS (default 3 hours)
   ↓ (block expires)
3 more OTP sends allowed
   ↓ (3rd one sent)
BLOCKED for OTP_LONG_BLOCK_HOURS (default 24 hours) - and this
long-term block keeps RE-APPLYING every time the limit is hit again,
so the system can never be abused indefinitely, while a genuine user
who waits it out can always get back in.
```
All of this logic lives in one method,
`OTPService._register_send_and_maybe_block()`, so you can tune it
without touching views or serializers at all.

### What never happens (security rules baked into the code)
- The raw OTP is **never** written to a log, a database row, or an API
  response — only a keyed HMAC-SHA256 hash of it is stored (in Redis,
  with an expiry).
- OTP comparison uses `hmac.compare_digest()`, not `==`, to avoid
  timing attacks.
- Every OTP is deleted immediately after a successful verification —
  it can never be reused.

---

## 7. Database design (PostgreSQL)

Only one table matters here: `users` (see `authentication/models.py`).

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | primary key |
| `name` | CharField | required |
| `country_code` | CharField | defaults to `+91` |
| `mobile_number` | CharField | **unique**, indexed, stored in E.164 format e.g. `+919876543210` |
| `email` | EmailField | nullable, **unique when present**, indexed |
| `is_mobile_verified` | Boolean | default False |
| `is_email_verified` | Boolean | default False |
| `is_active` | Boolean | default True |
| `is_staff` | Boolean | default False — required for Django admin |
| `created_at` / `updated_at` | DateTime | auto-managed |

**Why PostgreSQL for this and Redis for OTPs?** This data is permanent
and needs strong guarantees: a mobile number must never be claimed
twice, an email must never be claimed twice, and we must never silently
lose a user's account. PostgreSQL's unique constraints and durability
are exactly what this needs — it's the opposite of the OTP data, which
is short-lived and disposable.

**Why is `email` nullable while `mobile_number` is required?** Because
a user can fully register and use the app with just a mobile number
(see the registration flow) — forcing an email up front would add
friction for no real benefit. Once they add an email later, the same
uniqueness rule applies to prevent two accounts from claiming it.

---

## 8. Django Admin panel

Visit `/admin/` and log in with a superuser account (see Step 6 above).
The user list shows: name, email, mobile number, country code, mobile
verified, email verified, active, created/updated timestamps — with
search (by name/email/mobile) and filters (by verification/active
status) enabled.

**OTPs are never visible in the admin, ever** — because they are never
stored in PostgreSQL at all. They only ever exist in Redis, hashed, for
a few minutes. There is nothing OTP-related for an admin to accidentally
see, by design, not by hiding a field.

---

## 9. Security checklist (what's implemented and why)

- ✅ **Secure OTP generation** — Python's `secrets` module (cryptographically
  secure), not `random`.
- ✅ **OTP expiration** — Redis TTL, `OTP_EXPIRY_SECONDS`.
- ✅ **OTP verification attempt limits** — `OTP_MAX_VERIFY_ATTEMPTS`, stops brute force.
- ✅ **OTP resend rate limiting** — cooldown + escalating blocks, see section 6.
- ✅ **API throttling** — DRF's built-in `AnonRateThrottle`/`UserRateThrottle`
  as a second, independent layer of protection on top of the Redis logic.
- ✅ **HTTPS recommendation** — always run this behind HTTPS in production
  (e.g. via a reverse proxy like nginx or a platform load balancer);
  Django itself doesn't terminate TLS.
- ✅ **Secure JWT config** — short access token life, refresh rotation +
  blacklisting (see section 5).
- ✅ **CORS configuration** — via `django-cors-headers`, allowed origins
  read from `.env` (`CORS_ALLOWED_ORIGINS`).
- ✅ **CSRF** — DRF's JWT auth is not session/cookie based, so CSRF
  doesn't apply to the API itself; Django's CSRF protection still
  covers the browser-based Admin panel as usual.
- ✅ **Environment-based secrets** — nothing in this repo hard-codes a
  real secret; everything comes from `.env` via `python-decouple`.
- ✅ **OTPs never logged, never returned in responses.**
- ✅ **MSG91 / SMTP credentials never in source code.**
- ✅ **Phone numbers validated & normalized** — via the `phonenumbers` library.
- ✅ **Email validated** — via DRF's `EmailField`.
- ✅ **Some user-enumeration protection** — e.g. `/login/mobile/` returns
  the same error whether a mobile number doesn't exist or simply isn't
  verified yet, so an attacker can't tell those two cases apart.

One honest trade-off: `/register/` and `/login/email/` DO reveal
whether a specific mobile/email is already registered (via the 409/404
responses), because the spec's example flows depend on the frontend
knowing this to decide which screen to show next. If stricter
enumeration resistance is required later, these messages can be made
more generic at the cost of slightly worse UX.

---

## 10. Beginner-friendly design notes

- No design patterns beyond plain functions/classes and Django's own
  conventions (models, serializers, views). No repositories, no
  abstract factories, no signals-based magic.
- Every service class answers, in its own docstring: why does this
  exist, what does it receive, what does it return.
- Views only ever do 3 things: validate → call a service → return a
  response. If you need to change *how* OTPs work, you only ever touch
  `otp_service.py` — not every view that happens to send an OTP.
- To swap SMS providers later: only rewrite `msg91_service.py`. The
  rest of the project calls `send_otp(mobile, otp)` and doesn't care
  how it's implemented.
