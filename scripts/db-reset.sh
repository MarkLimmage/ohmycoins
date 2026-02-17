#!/bin/bash
set -e

# Database Reset Utility for Oh My Coins
# Quickly clears and re-seeds the database with fresh dev data

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1090
    . .env
    set +a
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Parse command line arguments
SKIP_CONFIRMATION=false
NO_REAL_DATA=false
USER_COUNT=${SEED_USER_COUNT:-10}
ALGORITHM_COUNT=${SEED_ALGORITHM_COUNT:-15}
SESSION_COUNT=${SEED_AGENT_SESSION_COUNT:-20}

while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes)
            SKIP_CONFIRMATION=true
            shift
            ;;
        --no-real-data)
            NO_REAL_DATA=true
            shift
            ;;
        --users)
            USER_COUNT="$2"
            shift 2
            ;;
        --algorithms)
            ALGORITHM_COUNT="$2"
            shift 2
            ;;
        --agent-sessions)
            SESSION_COUNT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -y, --yes              Skip confirmation prompt"
            echo "  --no-real-data         Skip real API data collection (faster)"
            echo "  --users N              Number of users to generate (default: 10)"
            echo "  --algorithms N         Number of algorithms to generate (default: 15)"
            echo "  --agent-sessions N     Number of agent sessions to generate (default: 20)"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Full reset with confirmation"
            echo "  $0 -y                        # Skip confirmation"
            echo "  $0 --no-real-data            # Faster reset without API calls"
            echo "  $0 --users 20 --algorithms 30  # Custom data volume"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Check if database container is running
if ! docker compose ps db | grep -q "Up"; then
    echo -e "${RED}Error: Database container is not running${NC}"
    echo "Start it with: docker-compose up -d db"
    exit 1
fi

# Confirmation prompt
if [ "$SKIP_CONFIRMATION" = false ]; then
    echo -e "${YELLOW}⚠️  WARNING: This will delete all data and re-seed the database!${NC}"
    echo ""
    echo "Configuration:"
    echo "  Users: ${USER_COUNT}"
    echo "  Algorithms: ${ALGORITHM_COUNT}"
    echo "  Agent Sessions: ${SESSION_COUNT}"
    echo "  Real Data: $([ "$NO_REAL_DATA" = true ] && echo "No" || echo "Yes")"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Reset cancelled.${NC}"
        exit 0
    fi
fi

echo -e "${YELLOW}Stopping dependent services...${NC}"
docker compose stop backend frontend playwright 2>/dev/null || true

echo -e "${YELLOW}Clearing existing data...${NC}"
docker compose run --rm backend python -m app.utils.seed_data --clear

echo -e "${YELLOW}Seeding database with fresh dev data...${NC}"
SEED_CMD="python -m app.utils.seed_data --all --users ${USER_COUNT} --algorithms ${ALGORITHM_COUNT} --agent-sessions ${SESSION_COUNT}"
if [ "$NO_REAL_DATA" = true ]; then
    SEED_CMD="${SEED_CMD} --no-real-data"
fi

docker compose run --rm backend $SEED_CMD

echo -e "${GREEN}✓ Database reset complete!${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Start services: ${YELLOW}docker-compose up -d${NC}"
echo -e "  2. Access API docs: ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  3. Access frontend: ${YELLOW}http://localhost:5173${NC}"
echo ""
echo -e "To create a snapshot of this state:"
echo -e "  ${YELLOW}./scripts/db-snapshot.sh my-dev-snapshot${NC}"
