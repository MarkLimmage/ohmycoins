#!/bin/bash
#
# Security Audit Execution Script
# Sprint 2.10 - Track B Phase 3: Agent Security Audit
#
# Runs all security tests and generates a summary report
#

set -e  # Exit on error

echo "========================================="
echo "OhMyCoins BYOM Security Audit"
echo "Sprint 2.10 - Track B Phase 3"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to backend directory
cd "$(dirname "$0")/.."

echo "📋 Running security test suite..."
echo ""

# Run all security tests with verbose output
pytest backend/tests/security/ \
    -v \
    -m security \
    --tb=short \
    --color=yes \
    --durations=10

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo "========================================="
echo "Security Audit Summary"
echo "========================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All security tests passed!${NC}"
    echo ""
    echo "Security clearance: APPROVED"
    echo "The BYOM feature is ready for production deployment."
else
    echo -e "${RED}✗ Some security tests failed.${NC}"
    echo ""
    echo "Security clearance: PENDING"
    echo "Please review and fix failing tests before deployment."
fi

echo ""
echo "For detailed security report, see:"
echo "  docs/archive/history/sprints/sprint-2.10/TRACK_B_SECURITY_AUDIT_REPORT.md"
echo ""

exit $TEST_EXIT_CODE
