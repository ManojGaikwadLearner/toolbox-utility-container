"""
Shared exit codes so every subcommand behaves predictably in a pipeline.

This is what turns a script into a utility a CI system or orchestrator can
actually branch on, instead of a black box that just prints something and
returns 0 or 1. See the README's "Exit codes" table for the full reference
of which command uses which code and why.
"""

SUCCESS = 0

# wait-for: the target never became reachable within the timeout.
TIMEOUT = 1

# Any other command: unexpected/unclassified failure. Deliberately the same
# integer as TIMEOUT (both are the conventional Unix "generic failure" code)
# but named separately so each module's intent reads clearly at the call site.
GENERIC_ERROR = 1

# A required file/directory argument does not exist.
INPUT_NOT_FOUND = 2

# The input exists but could not be parsed or converted (bad CSV, bad JSON,
# unreadable image, etc).
PARSE_ERROR = 3

# A batch operation partially succeeded: some items were processed, others
# failed. Distinct from PARSE_ERROR (nothing could be processed at all).
PARTIAL_FAILURE = 4

# lint-json: one or more files failed schema validation. Distinct from
# PARSE_ERROR because the JSON itself parsed fine - it just doesn't conform.
VALIDATION_FAILED = 5
