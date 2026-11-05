#!/usr/bin/env bash
set -euo pipefail
trap 'status=$?; printf "::error file=.github/ireader/publish.sh,line=%s::Publisher failed with exit %s at: %s\n" "$LINENO" "$status" "$BASH_COMMAND"; exit "$status"' ERR
: "${RELEASE_TAG:?}" "${GH_REPO:?}" "${GITHUB_WORKSPACE:?}"
artifacts="$GITHUB_WORKSPACE/artifacts"
(cd "$artifacts" && sha256sum -c SHA256SUMS)
source_commit=$(python3 -c 'import json; print(json.load(open("../artifacts/build-metadata.json"))["source_commit"])')
[[ "$source_commit" =~ ^[a-f0-9]{40}$ ]]
[[ "$RELEASE_TAG" =~ ^[0-9]+\.[0-9]+\.[0-9]+-ireader\.[0-9]+$ ]]
git fetch "$artifacts/patched-source.bundle" refs/heads/ireader-release
if [[ "$(git rev-parse FETCH_HEAD)" != "$source_commit" ]]; then
  echo '::error::Source bundle commit does not match signed APK metadata.' >&2
  exit 1
fi
if [[ -n "$(git ls-tree -r --name-only "$source_commit" -- .github/workflows)" ]] ||
   [[ "$(git rev-list --count "$source_commit")" != 1 ]]; then
  echo '::error::Release source must be a standalone snapshot without workflows or upstream history.' >&2
  exit 1
fi
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
if [[ -n "$(git ls-remote --tags origin "refs/tags/$RELEASE_TAG")" ]]; then
  git fetch origin "refs/tags/$RELEASE_TAG"
  if [[ "$(git rev-parse 'FETCH_HEAD^{commit}')" != "$source_commit" ]]; then
    echo 'Existing release tag points to different source. Bump patch_revision; never overwrite a release tag.' >&2
    exit 1
  fi
else
  git tag -a "$RELEASE_TAG" "$source_commit" -m "Legado iReader $RELEASE_TAG"
  git push origin "refs/tags/$RELEASE_TAG"
fi
# A draft is resumable; a published release is immutable to this automation.
if gh release view "$RELEASE_TAG" --json isDraft > "$RUNNER_TEMP/ireader-release.json" 2> "$RUNNER_TEMP/ireader-release-error.txt"; then
  if [[ "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["isDraft"])' "$RUNNER_TEMP/ireader-release.json")" != True ]]; then
    echo 'This release is already published; refusing to replace its assets.'
    exit 0
  fi
else
  # The API detector already established that the release is absent or a draft.
  gh release create "$RELEASE_TAG" --verify-tag --draft --title "Legado iReader $RELEASE_TAG" --notes-file "$artifacts/RELEASE_NOTES.md"
fi
gh release upload "$RELEASE_TAG" "$artifacts"/*.apk "$artifacts"/mapping-*.txt "$artifacts/SHA256SUMS" "$artifacts/build-metadata.json" "$artifacts/ireader-patches.zip" "$artifacts/RELEASE_NOTES.md" --clobber
gh release edit "$RELEASE_TAG" --draft=false --latest --notes-file "$artifacts/RELEASE_NOTES.md"
