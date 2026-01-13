# Bug Report: PUT /publishers/{publisherId}/nodes/{nodeId}/versions/{versionId} endpoint broken

## Summary

The `PUT /publishers/{publisherId}/nodes/{nodeId}/versions/{versionId}` endpoint for updating changelog and deprecation status does not work with any authentication method.

## API Documentation Reference

https://docs.comfy.org/api-reference/registry/update-changelog-and-deprecation-status-of-a-node-version

## Expected Behavior

According to the documentation, the endpoint should accept Bearer token authentication and update the changelog/deprecated fields for a node version.

## Actual Behavior

### With Personal Access Token (created via POST /publishers/{publisherId}/tokens)

```bash
curl --request PUT \
  --url "https://api.comfy.org/publishers/{publisherId}/nodes/{nodeId}/versions/{versionId}" \
  --header "Authorization: Bearer <personal_access_token>" \
  --header "Content-Type: application/json" \
  --data '{"changelog": "Test", "deprecated": false}'
```

**Response:** `401 Unauthorized`
```json
{"message":"invalid auth token"}
```

## Additional Testing

| Authentication Method | Result |
|-----------------------|--------|
| `Authorization: Bearer <personal_access_token>` | 401 "invalid auth token" |
| `Authorization: <token>` (no Bearer prefix) | 401 "token is not in Bearer format" |
| Token in request body | 401 "missing auth token for path" |
| `X-API-Key: <token>` header | 401 "missing auth token for path" |

## Notes

- The same personal access token works correctly for `POST /publishers/{publisherId}/nodes/{nodeId}/versions` (publishing new versions via comfy-cli)
- This suggests the PUT endpoint may not accept personal access tokens

## Impact

Unable to automate changelog updates via GitHub Actions after publishing new versions. Currently the only workaround is manual updates via the registry website.
