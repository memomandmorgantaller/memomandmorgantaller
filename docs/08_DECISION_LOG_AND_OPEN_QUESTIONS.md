# Design decision history and remaining decisions

## Confirmed through discussion
- Initial objective: offline/local intelligent tool to file large industrial RFP packages into existing SharePoint Online folder structure.
- Project selected by user; not automatically inferred.
- Individual document classification; not package-level folder preservation.
- Existing historical, correctly filed examples are available conceptually; none supplied yet.
- Desired structure screenshot: nine named folders with numbered prefixes.
- Problematic CS202-like source screenshot: mixed root files, numerous drawing/specification ZIPs, commercial documents and pre-existing addenda/clarifications.
- Addenda handling = preserve together (physically leaf files in 06), vendor drawings = contextual, internal destination structure = flat.
- ZIP handling = extract each file; original archive retained separately.
- Progressive autonomy; orchestrated local specialist profiles; deterministic rules and limited publishing service.
- Windows dev workstation with eventual internal server.
- User has software installation access and expects to test with a sanitized package.

## Assumptions / defaults, not confirmed
- Unknown/unsupported/unparseable → human review.
- Different-content filename collisions → human review, no auto renaming.
- Identical bytes in separate source locations → all occurrence lineage preserved, potential single output after approval.
- No automatic splitting of compound documents.
- All local exports require human approval initially.
- Exact Graph permissions, site mappings, Entra tenant, retention and identity controls require IT signoff.
- No attachment containing the actual sanitized RFP has yet been received in this conversation.

## Questions to resolve with business owner before production
1. How are official addenda/clarification sources authenticated? Is ZIP/folder membership enough if there's conflicting evidence?
2. What is the source-of-truth revision policy, especially revised file originally issued under addenda and newer project-issued drawings?
3. How to name files in a flat destination on collision (currently review)?
4. Any permissible metadata columns in SharePoint and how to handle document numbers/revisions?
5. Preservation and retention policy for original packages and derived analysis artifacts?
6. What constitutes a project-specific start-here document versus commercial bidder instructions?
7. Who can approve, override, manage filing policy, grant automatic filing by category, and audit?
8. Which CAD, legacy XLS/DOC and scanned formats exist in actual packages, and which need priority support?
9. Does the customer's source structure reveal legally relevant grouping that must be preserved in metadata?
10. What are workstation CPU/GPU/RAM, local AI model licensing and IT-approved packages?
