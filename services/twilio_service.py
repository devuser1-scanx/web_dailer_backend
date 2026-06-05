# services/twilio_service.py

from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.twiml.voice_response import VoiceResponse, Dial

from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_API_KEY_SID,
    TWILIO_API_KEY_SECRET,
    TWILIO_TWIML_APP_SID,
    TWILIO_PHONE_NUMBER,
    CLIENT_FORWARD_NUMBER,
    ENABLE_IVR,
)


def generate_voice_token(identity: str) -> str:
    """
    Generate a temporary Twilio Voice SDK access token for browser calling.
    """

    if not all([
        TWILIO_ACCOUNT_SID,
        TWILIO_API_KEY_SID,
        TWILIO_API_KEY_SECRET,
        TWILIO_TWIML_APP_SID,
    ]):
        raise ValueError("Missing Twilio Voice SDK configuration")

    token = AccessToken(
        TWILIO_ACCOUNT_SID,
        TWILIO_API_KEY_SID,
        TWILIO_API_KEY_SECRET,
        identity=identity,
    )

    voice_grant = VoiceGrant(
        outgoing_application_sid=TWILIO_TWIML_APP_SID,
        incoming_allow=False,
    )

    token.add_grant(voice_grant)

    return token.to_jwt()


def build_outgoing_call_twiml(to_number: str) -> str:
    """
    TwiML returned to Twilio when browser initiates outbound call.
    """

    response = VoiceResponse()

    dial = Dial(
        caller_id=TWILIO_PHONE_NUMBER,
        timeout=30,
        record="record-from-answer-dual",
    )

    dial.number(
        to_number,
        status_callback_event="initiated ringing answered completed",
        status_callback="/voice/status",
        status_callback_method="POST",
    )

    response.append(dial)

    return str(response)


def build_current_forwarding_twiml() -> str:
    """
    Preserve current incoming forwarding behavior.

    Caller calls ScanX number → Twilio forwards to CLIENT_FORWARD_NUMBER.
    IVR stays dormant unless ENABLE_IVR=true in future.
    """

    response = VoiceResponse()

    if ENABLE_IVR:
        # Dormant placeholder. Do not enable now.
        response.say("IVR is not active yet.")
        response.hangup()
        return str(response)

    if not CLIENT_FORWARD_NUMBER:
        response.say("Sorry, no forwarding number is configured.")
        response.hangup()
        return str(response)

    dial = Dial(
        timeout=30,
        action="/voice/status",
        method="POST",
    )

    dial.number(
        CLIENT_FORWARD_NUMBER,
        status_callback_event="initiated ringing answered completed",
        status_callback="/voice/status",
        status_callback_method="POST",
    )

    response.append(dial)

    return str(response)