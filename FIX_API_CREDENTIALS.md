# 🔧 Fix OANDA API Credentials

## ⚠️ Current Issue

Your OANDA API token is returning **401 Unauthorized** errors. This means:
- The API token has expired
- The token doesn't have proper permissions
- The account ID might be incorrect

## 🔑 How to Fix (5 minutes)

### Step 1: Log into OANDA
1. Go to [https://www.oanda.com](https://www.oanda.com)
2. Log into your account

### Step 2: Revoke Old Token
1. Go to **Account Settings** → **API Access**
2. Find your existing token
3. Click **Revoke** to delete it

### Step 3: Generate New Token
1. Click **Generate** to create a new API token
2. **IMPORTANT**: Copy the token immediately (you can't see it again!)
3. Also copy your Account ID

### Step 4: Update Configuration Files

Edit `config/oanda_demo.cfg`:
```ini
[oanda]
account_id=YOUR_NEW_ACCOUNT_ID
access_token=YOUR_NEW_TOKEN_HERE
account_type=practice
hostname=api-fxpractice.oanda.com
```

Edit `config/oanda_live.cfg` (if you have a separate live account):
```ini
[oanda]
account_id=YOUR_LIVE_ACCOUNT_ID
access_token=YOUR_LIVE_TOKEN_HERE
account_type=live
hostname=api-fxtrade.oanda.com
```

### Step 5: Test Connection
```bash
python test_system_comprehensive.py
```

You should see all tests pass!

## 🎯 What Permissions Are Needed

Make sure your API token has these permissions:
- ✅ Read account information
- ✅ Read pricing data
- ✅ Read historical data
- ✅ Create/modify/close orders
- ✅ Read positions

## 🔒 Security Tips

1. **Never share your API token**
2. **Don't commit tokens to Git** (they're in .gitignore)
3. **Regenerate tokens periodically**
4. **Use practice account for testing**

## ❓ Still Having Issues?

If you continue to get 401 errors after updating:
1. Double-check the account ID matches exactly
2. Ensure no extra spaces in the config file
3. Verify the token was copied completely
4. Check that the account type matches (practice vs live)
5. Make sure the token has all required permissions

---

**Once fixed, you can run:**
```bash
python UltimateTradingInterface.py
