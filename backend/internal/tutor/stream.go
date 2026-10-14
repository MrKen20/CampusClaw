package tutor

import (
	"campusclaw/backend/internal/auth"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

func frame(w http.ResponseWriter, event string, payload any) error {
	data, e := json.Marshal(payload)
	if e != nil {
		return e
	}
	if _, e = fmt.Fprintf(w, "event: %s\ndata: %s\n\n", event, data); e != nil {
		return e
	}
	return http.NewResponseController(w).Flush()
}

// SendMessage validates before starting the stream. Locks are per conversation, never global.
// @api {"method":"POST","path":"/api/conversations/{id}/messages","summary":"在锁定智能体的会话中流式提问","auth":"login","status":200,"request":{"type":"object","properties":{"content":{"type":"string","minLength":2,"maxLength":500}},"required":["content"]},"response":{"type":"string"},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用","409":"该会话正在生成"},"stream":true,"description":"真实SSE：meta先带skill/citations；delta.text是新增片段；助手消息落库后done.message_id；流后失败error，已发片段存为partial。不同会话可并行，同一会话并发409。正文agent_id/history/class_id被忽略。","example":"event: meta\ndata: {\"status\":\"ok\",\"skill\":null,\"citations\":[]}\n\nevent: delta\ndata: {\"text\":\"先看这一步\"}\n\nevent: done\ndata: {\"message_id\":1}\n\n"}
func (s *Service) SendMessage(w http.ResponseWriter, r *http.Request) {
	u, _ := auth.FromContext(r.Context())
	c, e := s.conversation(r.Context(), pathID(r), u)
	if e != nil {
		resourceError(w, e)
		return
	}
	var in struct {
		Content string `json:"content"`
	}
	if !body(w, r, &in) {
		return
	}
	in.Content = strings.TrimSpace(in.Content)
	n := len([]rune(in.Content))
	if n < 2 || n > 500 {
		fail(w, 400, "问题须为2到500字")
		return
	}
	if _, loaded := s.busy.LoadOrStore(c.ID, true); loaded {
		fail(w, 409, "该会话正在生成，请等待或停止后再发送")
		return
	}
	defer s.busy.Delete(c.ID)
	a, e := s.agent(r.Context(), c.AgentID, u.ClassID, false)
	if e != nil {
		resourceError(w, e)
		return
	}
	skills, e := s.skills(r.Context(), u.ClassID, a.ID)
	if e != nil {
		dbFail(w)
		return
	}
	sk := Route(skills, in.Content)
	tx, e := s.DB.BeginTx(r.Context(), nil)
	if e != nil {
		dbFail(w)
		return
	}
	var count int
	e = tx.QueryRowContext(r.Context(), `SELECT COUNT(*) FROM messages WHERE conversation_id=?`, c.ID).Scan(&count)
	if e == nil {
		_, e = tx.ExecContext(r.Context(), `INSERT INTO messages(conversation_id,role,content,citations_json) VALUES(?,'user',?,'[]')`, c.ID, in.Content)
	}
	if e == nil {
		if count == 0 {
			_, e = tx.ExecContext(r.Context(), `UPDATE conversations SET title=?,updated_at=CURRENT_TIMESTAMP WHERE id=?`, short(in.Content, 24), c.ID)
		} else {
			_, e = tx.ExecContext(r.Context(), `UPDATE conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=?`, c.ID)
		}
	}
	if e != nil {
		tx.Rollback()
		dbFail(w)
		return
	}
	if e = tx.Commit(); e != nil {
		dbFail(w)
		return
	}
	hits, e := s.Searcher.SearchBound(r.Context(), u.ClassID, in.Content, a.MaterialIDs, 4)
	if e != nil {
		dbFail(w)
		return
	}
	history, e := s.messages(r.Context(), c.ID, true)
	if e != nil {
		dbFail(w)
		return
	}
	messages, cites := BuildMessages(a, sk, history, hits)
	w.Header().Set("Content-Type", "text/event-stream; charset=utf-8")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")
	if e = frame(w, "meta", map[string]any{"status": "ok", "skill": sk, "citations": cites, "agent_id": a.ID}); e != nil {
		return
	}
	filter := CitationFilter{max: len(cites)}
	var answer strings.Builder
	emit := func(text string) error {
		if text == "" {
			return nil
		}
		answer.WriteString(text)
		return frame(w, "delta", map[string]string{"text": text})
	}
	ctx, cancel := context.WithTimeout(r.Context(), 90*time.Second)
	defer cancel()
	streamErr := s.Chat.Stream(ctx, messages, func(text string) error { return emit(filter.Feed(text, false)) })
	if streamErr == nil {
		streamErr = emit(filter.Feed("", true))
	}
	status := "complete"
	if streamErr != nil {
		status = "partial"
	}
	// Request cancellation cannot prevent recording text already sent to the student.
	saveCtx, saveCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer saveCancel()
	if answer.Len() == 0 {
		_ = frame(w, "error", map[string]string{"error": "回答未生成，请稍后重试"})
		return
	}
	cj, _ := json.Marshal(cites)
	skillName := ""
	if sk != nil {
		skillName = sk.Name
	}
	res, e := s.DB.ExecContext(saveCtx, `INSERT INTO messages(conversation_id,role,content,citations_json,skill_name,status) VALUES(?,'assistant',?,?,?,?)`, c.ID, answer.String(), string(cj), skillName, status)
	if e != nil {
		_ = frame(w, "error", map[string]string{"error": "回答保存失败"})
		return
	}
	id, e := res.LastInsertId()
	if e != nil {
		_ = frame(w, "error", map[string]string{"error": "回答保存失败"})
		return
	}
	if streamErr != nil {
		_ = frame(w, "error", map[string]any{"error": "回答中断，已保存生成的部分内容", "message_id": id})
		return
	}
	_ = frame(w, "done", map[string]int64{"message_id": id})
}
