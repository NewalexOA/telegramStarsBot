import pytest
from models.referral import ReferralLink, Referral

@pytest.mark.asyncio
async def test_referral_link_creation(db_session):
    """Test ReferralLink model"""
    async with db_session.begin():
        link = ReferralLink(user_id=123456, code="test_code_1")
        db_session.add(link)
        await db_session.flush()
        
        assert link.id is not None
        assert link.user_id == 123456
        assert link.code == "test_code_1"

@pytest.mark.asyncio
async def test_referral_creation(db_session):
    """Test Referral model"""
    async with db_session.begin():
        link = ReferralLink(user_id=123456, code="test_code_2")
        db_session.add(link)
        await db_session.flush()
        
        referral = Referral(
            referrer_id=link.user_id,
            referred_id=789012,
            link_id=link.id
        )
        db_session.add(referral)
        await db_session.flush()
        
        assert referral.id is not None
        assert referral.referrer_id == 123456
        assert referral.referred_id == 789012