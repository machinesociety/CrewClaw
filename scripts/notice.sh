echo "$CI_API_V4_URL/projects/$CI_PROJECT_ID/pipelines/$CI_PIPELINE_ID/jobs"
JOB_STATUS=$(curl --silent --header "Private-Token: $GITLAB_TOKEN" \
        "$CI_API_V4_URL/projects/$CI_PROJECT_ID/pipelines/$CI_PIPELINE_ID/jobs" \
      | jq -r '.[] | select(.stage == "build") | .status')

# 准备通知内容
if [ "$JOB_STATUS" = "failed" ]; then
  STATUS="❌ 构建失败"
  COLOR="red"
else
  STATUS="✅ 构建成功"
  COLOR="green"
fi
# 发送飞书消息（需要提前获取飞书机器人webhook）
curl -X POST -H "Content-Type: application/json" \
-d '{
  "msg_type": "interactive",
  "card": {
    "elements": [
      {"tag": "div", "text": {"content": "项目: '"$CI_PROJECT_NAME"'"}},
      {"tag": "div", "text": {"content": "分支: '"$CI_COMMIT_BRANCH"'"}},
      {"tag": "div", "text": {"content": "提交: '"$CI_COMMIT_SHORT_SHA"'"}},
      {"tag": "div", "text": {"content": "状态: '"$STATUS"'"}},
      {"tag": "div", "text": {"content": "查看: '"$CI_PIPELINE_URL"'"}}
    ],
    "header": {"title": {"content": "CI/CD 构建通知", "tag": "plain_text"}, "template": "'"$COLOR"'"},
    "actions": [{"tag": "button", "text": {"content": "查看详情", "tag": "plain_text"}, "url": "'"$CI_PIPELINE_URL"'"}]
  }
}' \
$FEISHU_WEBHOOK
