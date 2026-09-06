# Field-sales UX research and decisions

Public primary documentation for representative retail-execution systems was reviewed. This was not an audit of every promoter application or a hands-on competitor evaluation.

## Useful patterns

- [Repsly merchandising](https://www.repsly.com/solutions/merchandising): branch inventory access, replenishment, reporting and display review informed connections between Stock, Requests, Shelf & Photos and Home's next actions.
- [Salesforce store-visit workflow](https://trailhead.salesforce.com/content/learn/modules/consumer-goods-cloud-offline-mobile-app-for-field-reps/complete-store-visit-tasks-sync-data): visit tasks and synchronization highlight the distinction between recording on a device and organizational receipt.
- [Salesforce retail execution](https://www.salesforce.com/products/consumer-goods-cloud/retail-execution/): start-of-day views and offline work informed the compact dashboard and local recording. This prototype has local storage, not a production offline sync engine.
- [Axsy on Salesforce AppExchange](https://appexchange.salesforce.com/appxListingDetail?listingId=a0N3A00000G0vE8UAJ&scrollTo=additional-details&tab=d): task access, documents and order capture support short forms and accessible training. Route planning is outside this sitemap.

## Risks avoided — our design assessment

1. Metrics without actions: use a daily target card and direct task links.
2. Lost field-report drafts: preserve sale, count and request drafts across navigation.
3. Local saves mistaken for server receipt: explicitly identify local records, sample data and future review.
4. Counts treated as authorized inventory adjustments: preserve observations and discrepancy reasons separately.
5. Biometric device unlock mistaken for verified employee attendance: keep them separate.
6. Unexpected photos/location access: user-initiated permissions and failure handling. Gallery photos retain their source label; coordinates represent the current device location, not proof of original capture.
7. Unsupported AI scores and rewards: no automatic visual grading; points are illustrative.
8. Scope creep: no Ads account, public signup, social feed, payroll, AI assistant, route optimization or supervisor approvals inside the promoter prototype.

These are design risks, not claims that the vendors above implemented their products badly.

## Native references

- [Expo ImagePicker SDK 55](https://docs.expo.dev/versions/v55.0.0/sdk/imagepicker/): camera/library and permissions; microphone disabled.
- [Expo Location SDK 55](https://docs.expo.dev/versions/v55.0.0/sdk/location/): foreground location.
- [Expo FileSystem SDK 55](https://docs.expo.dev/versions/v55.0.0/sdk/filesystem/): copy selected images into app documents rather than keep only temporary picker files.

## Decisions before backend integration

Confirm catalog/prices, branches, shift rules, targets/rewards, relocation meaning (currently stock relocation), approvals and whether sales adjust stock. Production offline support needs durable operation IDs, retries, conflict resolution, permission revocation and server reconciliation.
