# Azure Key Vault Integration Setup

Your app is now configured to retrieve `EntraClientSecret` from Azure Key Vault with a fallback to environment variables for local development.

## How It Works

The `get_secret()` function in `auth.py`:
1. **First**: Attempts to retrieve the secret from Azure Key Vault (if `AZURE_KEYVAULT_URL` is set)
2. **Fallback**: Uses environment variables (`.env` file) if Key Vault is not available
3. This allows seamless local development and production deployment

## Local Development (Current Setup)

Since `AZURE_KEYVAULT_URL` is not set in your `.env`, the app will:
- Skip Key Vault lookup
- Use `EntraClientSecret` from `.env` file
- Everything works as-is ✓

## Production Setup on Azure App Service

### Step 1: Create an Azure Key Vault

```bash
# Create a resource group (if you don't have one)
az group create --name myResourceGroup --location eastus

# Create a Key Vault
az keyvault create --name my-vault --resource-group myResourceGroup --location eastus
```

**Note**: Key Vault names must be globally unique and contain only alphanumeric characters and hyphens (no underscores).

### Step 2: Add Your Secret to Key Vault

```bash
az keyvault secret set --vault-name my-vault --name EntraClientSecret --value "YOUR_CLIENT_SECRET_HERE"
```

### Step 3: Create a Managed Identity for Your App Service

```bash
# Enable managed identity on your App Service
az webapp identity assign --name myAppName --resource-group myResourceGroup
```

### Step 4: Grant Key Vault Access to Your App Service

```bash
# Get the managed identity object ID
IDENTITY_ID=$(az webapp identity show --name myAppName --resource-group myResourceGroup --query principalId -o tsv)

# Grant the identity permission to read secrets
az keyvault set-policy --name my-vault --object-id $IDENTITY_ID --secret-permissions get list
```

### Step 5: Configure Environment Variables on Azure App Service

Set these variables in App Service Configuration → Application settings:

```
AZURE_KEYVAULT_URL = https://my-vault.vault.azure.net/
ENTRA_CLIENT_ID = 64046e43-458d-43ab-ae5e-a4e2922f21ea
ENTRA_AUTHORITY = https://login.microsoftonline.com/a8abbdba-2a97-413e-b6f6-0593a2c7df01
ENTRA_REDIRECT_URI = https://myappname.azurewebsites.net/auth/callback
```

**Note**: 
- `EntraClientSecret` is NOT stored as an app setting—it comes from Key Vault
- `ENTRA_REDIRECT_URI` must match your actual production domain

## Authentication Method

The code uses `DefaultAzureCredential()` from the Azure SDK, which automatically uses the App Service's Managed Identity to authenticate to Key Vault. This is secure and requires no additional secrets in your configuration.

## Testing

### Local testing (with .env):
Your app will print:
```
[KEY_VAULT] ⚠ Could not retrieve 'EntraClientSecret' from Key Vault: (error details)
[KEY_VAULT] Using fallback environment variable: EntraClientSecret
```

### Production testing (with Key Vault):
Your app will print:
```
[KEY_VAULT] ✓ Successfully retrieved 'EntraClientSecret' from Azure Key Vault
```

## Troubleshooting

If your app can't connect to Key Vault in production:
1. Check Managed Identity is enabled: `az webapp identity show --name myAppName --resource-group myResourceGroup`
2. Verify Key Vault access policy: `az keyvault show-deleted --name my-vault` 
3. Check if the secret exists: `az keyvault secret show --vault-name my-vault --name EntraClientSecret`
4. Review App Service logs in Azure Portal

## Security Best Practices

✓ Never commit secrets to Git (they're already in .gitignore)
✓ Use Managed Identity instead of stored credentials
✓ Rotate secrets regularly
✓ Enable Key Vault audit logging
✓ Use Key Vault network policies to restrict access

## Adding More Secrets

If you need to add more secrets (like `EntraClientId` for other configs):
1. Add to Key Vault: `az keyvault secret set --vault-name my-vault --name EntraClientId --value "..."`
2. Update `auth.py` to retrieve it: `CLIENT_ID = get_secret('EntraClientId', 'ENTRA_CLIENT_ID')`
3. This allows the same fallback pattern for all secrets
