# Publish the prepared source repository

Public publication is **not verified**. No remote URL or account authentication has been supplied to this task.

## Use the curated snapshot, not private development history

Use `packages/PathSnap_Publication_Source/` on this laptop, or extract `PathSnap_Publication_Source.zip` elsewhere. The snapshot excludes raw inputs, cache/per-point outputs, detailed coordinate maps/screenshots, the separate PDF deliverable and all prior `.git` history. It retains source, required model artifacts, aggregate metrics/configurations, dependency pins and generation code.

`SOURCE_COMMIT.txt` identifies the final private-workspace commit. Runtime/model members are checked against that commit by the submission verifier. The publication repository has its own commit history; its commit hash can differ without changing the implementation. Preserve the private development repository as the detailed audit trail.

## Steps requiring your GitHub account

1. Review `docs/LICENSING_AND_DATA.md`, the inclusion manifest and secret/file-size scan. Confirm dataset-derived publication permissions with the organizer.
2. Set the Git author name/email you intend to make public. You may use your GitHub-provided no-reply address; do not enter account passwords or tokens into project files.
3. In GitHub, create an empty **public** repository under the correct team account. Avoid adding a remote README/license until the local files are ready. Select a source license only with team approval; none was inferred here.
4. Open PowerShell in the publication snapshot. If it was extracted from the ZIP and has no `.git` directory, initialize it:

```powershell
git init -b main
git add .
git commit -m "Submit audited PathSnap source and aggregate experiments"
```

5. Add the actual URL from GitHub, replacing the example:

```powershell
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
git push -u origin main
```

Use Git's approved sign-in flow. Do not put a token in a remote URL. If `origin` already exists, inspect `git remote -v` and confirm it is the intended repository before changing or pushing.

6. Open the repository URL while logged out/private browsing. Verify README, full source, model/configuration artifacts, dependencies, aggregate results and map-generation code are accessible. Record the URL and public commit hash.
7. Submit the public URL and the single final PDF through the event's required channel. The publication snapshot deliberately omits the PDF/location-bearing outputs until their publication permissions are confirmed; separate report submission is still required.

## Size and hygiene checks

`scripts/submission_checks.py` checks the publication snapshot, selected implementation, deployment ZIPs and repository for secrets, oversized files and unintended inputs. GitHub's documented regular-file thresholds are a warning above 50 MiB and a block above 100 MiB; see [GitHub's official large-file documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). No model artifact in this project approaches those thresholds. Do not upload the complete-local or backend deployment ZIP as a public release asset: they contain supplied trip data.

After changing team details or adding real console evidence, rebuild and visually review the report and regenerate packages/provenance. Do not retrain or tune the frozen model to complete publication.
