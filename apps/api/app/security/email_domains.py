"""Email-domain helpers for tenant onboarding (Work Order B1).

`domain_of` extracts the lowercased domain from an email address.
`is_generic_provider` flags consumer mailbox providers that must never
auto-join a client (a gmail.com address tells us nothing about which
organization the person belongs to).
"""

from __future__ import annotations

# Consumer mailbox providers. A person at one of these could belong to any
# organization (or none), so we never auto-join them to a client by domain.
GENERIC_EMAIL_PROVIDERS: frozenset[str] = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "outlook.com",
        "hotmail.com",
        "live.com",
        "msn.com",
        "yahoo.com",
        "ymail.com",
        "aol.com",
        "icloud.com",
        "me.com",
        "mac.com",
        "proton.me",
        "protonmail.com",
        "pm.me",
        "gmx.com",
        "mail.com",
        "zoho.com",
        "yandex.com",
        "fastmail.com",
        "hey.com",
        "qq.com",
        "163.com",
        "126.com",
    }
)


def domain_of(email: str) -> str:
    """Lowercased domain part of an email, or '' if there is no '@'."""
    _, _, domain = email.partition("@")
    return domain.strip().lower()


def is_generic_provider(domain: str) -> bool:
    return domain.lower() in GENERIC_EMAIL_PROVIDERS
