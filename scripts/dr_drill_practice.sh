#!/bin/bash
#
# DR Drill Practice Mode
# Interactive practice session for team training
#

set -e

echo "🎓 DR Drill Practice Mode"
echo "========================"
echo ""
echo "This is an interactive training session."
echo "You will be guided through DR procedures step by step."
echo ""

read -p "Press Enter to start practice session..."

# Quiz function
quiz() {
    local question=$1
    local correct_answer=$2
    
    echo ""
    echo "❓ $question"
    read -p "Your answer: " user_answer
    
    if [ "$user_answer" = "$correct_answer" ]; then
        echo "✅ Correct!"
    else
        echo "❌ Incorrect. The answer is: $correct_answer"
    fi
}

# Practice Phase 1
echo ""
echo "=== Phase 1 Practice:  Infrastructure ==="
echo ""

quiz "What is the first AWS command to provision a server?" "aws ec2 run-instances"
quiz "What instance type should be used for DR?" "t3.xlarge"
quiz "How much storage is required?" "100GB"

echo ""
echo "Phase 1 Commands to memorize:"
cat <<'EOF'

1.  Provision server: 
   aws ec2 run-instances --image-id ami-xxx --instance-type t3.xlarge ... 

2. Wait for instance: 
   aws ec2 wait instance-running --instance-ids $INSTANCE_ID

3. Get public IP:
   aws ec2 describe-instances --instance-ids $INSTANCE_ID \
       --query 'Reservations[0].Instances[0].PublicIpAddress'

EOF

read -p "Press Enter to continue to Phase 2..."

# Practice Phase 2
echo ""
echo "=== Phase 2 Practice: Application Deployment ==="
echo ""

quiz "What is the first step in application deployment?" "Clone repository" 
quiz "Which branch/tag should be checked out?" "v1.0.0"
quiz "Where should environment variables be stored?" ". env file"

echo ""
echo "Phase 2 Commands to memorize:"
cat <<'EOF'

1. Clone repository:
   git clone https://github.com/your-org/mcp-memory-server.git

2. Checkout version:
   git checkout v1.0.0

3. Pull images:
   docker-compose pull

EOF

read -p "Press Enter to continue to Phase 3..."

# Practice Phase 3
echo ""
echo "=== Phase 3 Practice: Data Recovery ==="
echo ""

quiz "Where are off-site backups stored?" "S3"
quiz "Which component is restored first?" "Prometheus"
quiz "How do you verify database integrity?" "PRAGMA integrity_check"

echo ""
echo "Phase 3 Commands to memorize:"
cat <<'EOF'

1. Download backups:
   aws s3 sync s3://mcp-backups/monitoring/ /var/backups/

2. Restore Prometheus:
   ./scripts/restore_prometheus.sh latest

3. Restore Application:
   ./scripts/restore_application.sh latest

EOF

read -p "Press Enter to continue to Phase 4..."

# Practice Phase 4
echo ""
echo "=== Phase 4 Practice: Verification ==="
echo ""

quiz "What script runs comprehensive verification?" "verify_recovery.sh"
quiz "What is the RTO target?" "4 hours"
quiz "What is the RPO target?" "1 hour"

echo ""
echo "Phase 4 Commands to memorize:"
cat <<'EOF'

1. Run verification: 
   ./scripts/verify_recovery.sh

2. Manual health check:
   curl http://localhost:8080/health

3. Check Prometheus data:
   curl 'http://localhost:9090/api/v1/query? query=up'

EOF

# Summary
echo ""
echo "========================="
echo "🎓 Practice Session Complete"
echo "========================="
echo ""
echo "Key Takeaways:"
echo "- Phase 1: Infrastructure takes ~60 minutes"
echo "- Phase 2: Deployment takes ~45 minutes"
echo "- Phase 3: Data recovery takes ~90 minutes"
echo "- Phase 4: Verification takes ~30 minutes"
echo "- Total RTO target: <4 hours"
echo ""
echo "Next Steps:"
echo "- Review DR drill plan:  docs/disaster-recovery/dr-drill-plan.md"
echo "- Run simulation: ./scripts/simulate_dr_drill.sh"
echo "- Schedule actual drill with team"
echo ""
