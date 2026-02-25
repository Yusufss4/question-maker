"""Context processors for templates."""
from core.models import Voter


def voter_context(request):
    """Add current voter to context when logged in (via session)."""
    if not request.session.get("voter_id"):
        return {}
    try:
        voter = Voter.objects.get(pk=request.session["voter_id"], is_active=True)
        return {"voter": voter}
    except Voter.DoesNotExist:
        return {}
