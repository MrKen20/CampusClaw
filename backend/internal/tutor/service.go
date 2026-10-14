package tutor

import (
	"campusclaw/backend/internal/auth"
	"campusclaw/backend/internal/retrieval"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"strings"
	"sync"
)

type Service struct {
	DB       *sql.DB
	Searcher *retrieval.Searcher
	Chat     *retrieval.ChatClient
	busy     sync.Map
}

func NewService(d *sql.DB, search *retrieval.Searcher, chat *retrieval.ChatClient) *Service {
	return &Service{DB: d, Searcher: search, Chat: chat}
}
func jsonResponse(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
func fail(w http.ResponseWriter, status int, msg string) {
	jsonResponse(w, status, map[string]string{"error": msg})
}
func missing(w http.ResponseWriter) { fail(w, 404, "资源不存在") }
func dbFail(w http.ResponseWriter)  { fail(w, 503, "服务暂时不可用") }
func body(w http.ResponseWriter, r *http.Request, v any) bool {
	r.Body = http.MaxBytesReader(w, r.Body, 64<<10)
	dec := json.NewDecoder(r.Body)
	if e := dec.Decode(v); e != nil {
		fail(w, 400, "请求必须是合法 JSON")
		return false
	}
	return true
}
func pathID(r *http.Request) int64 { v, _ := strconv.ParseInt(r.PathValue("id"), 10, 64); return v }

type Agent struct {
	ID          int64   `json:"id"`
	Name        string  `json:"name"`
	Prompt      string  `json:"prompt"`
	Enabled     bool    `json:"enabled"`
	SkillIDs    []int64 `json:"skill_ids"`
	MaterialIDs []int64 `json:"material_ids"`
}
type AgentInput struct {
	Name        string  `json:"name"`
	Prompt      string  `json:"prompt"`
	Enabled     bool    `json:"enabled"`
	SkillIDs    []int64 `json:"skill_ids"`
	MaterialIDs []int64 `json:"material_ids"`
}

func (s *Service) agent(ctx context.Context, id, classID int64, requireEnabled bool) (Agent, error) {
	a := Agent{SkillIDs: []int64{}, MaterialIDs: []int64{}}
	q := `SELECT id,name,prompt,enabled FROM tutor_agents WHERE id=? AND class_id=?`
	if requireEnabled {
		q += ` AND enabled=TRUE`
	}
	e := s.DB.QueryRowContext(ctx, q, id, classID).Scan(&a.ID, &a.Name, &a.Prompt, &a.Enabled)
	if e != nil {
		return a, e
	}
	for _, x := range []struct {
		q    string
		dest *[]int64
	}{{`SELECT skill_id FROM tutor_agent_skills WHERE agent_id=? ORDER BY skill_id`, &a.SkillIDs}, {`SELECT material_id FROM tutor_agent_materials WHERE agent_id=? ORDER BY material_id`, &a.MaterialIDs}} {
		rows, e := s.DB.QueryContext(ctx, x.q, id)
		if e != nil {
			return a, e
		}
		for rows.Next() {
			var v int64
			if e = rows.Scan(&v); e != nil {
				rows.Close()
				return a, e
			}
			*x.dest = append(*x.dest, v)
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return a, e
		}
	}
	return a, nil
}
func resourceError(w http.ResponseWriter, e error) {
	if errors.Is(e, sql.ErrNoRows) {
		missing(w)
	} else {
		dbFail(w)
	}
}
// @api {"method":"GET","path":"/api/agents","summary":"列出本班智能体；学生只见启用者","auth":"login","status":200,"request":null,"response":{"type":"array","items":{"$ref":"#/components/schemas/Agent"}},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
func (s *Service) Agents(w http.ResponseWriter, r *http.Request) {
	u, _ := auth.FromContext(r.Context())
	q := `SELECT id FROM tutor_agents WHERE class_id=?`
	if u.Role != "teacher" {
		q += ` AND enabled=TRUE`
	}
	q += ` ORDER BY id`
	rows, e := s.DB.QueryContext(r.Context(), q, u.ClassID)
	if e != nil {
		dbFail(w)
		return
	}
	ids := []int64{}
	for rows.Next() {
		var id int64
		if e = rows.Scan(&id); e != nil {
			rows.Close()
			dbFail(w)
			return
		}
		ids = append(ids, id)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		dbFail(w)
		return
	}
	out := []Agent{}
	for _, id := range ids {
		a, e := s.agent(r.Context(), id, u.ClassID, u.Role != "teacher")
		if e != nil {
			resourceError(w, e)
			return
		}
		out = append(out, a)
	}
	jsonResponse(w, 200, out)
}
// @api {"method":"GET","path":"/api/agents/{id}","summary":"读取本班智能体","auth":"login","status":200,"request":null,"response":{"$ref":"#/components/schemas/Agent"},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
func (s *Service) Agent(w http.ResponseWriter, r *http.Request) {
	u, _ := auth.FromContext(r.Context())
	a, e := s.agent(r.Context(), pathID(r), u.ClassID, u.Role != "teacher")
	if e != nil {
		resourceError(w, e)
		return
	}
	jsonResponse(w, 200, a)
}
// @api {"method":"POST","path":"/api/agents","summary":"创建智能体并原子绑定本班资源","auth":"teacher","status":201,"request":{"$ref":"#/components/schemas/AgentInput"},"response":{"$ref":"#/components/schemas/Agent"},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
// @api {"method":"PUT","path":"/api/agents/{id}","summary":"修改提示词、启停与绑定；下一轮生效","auth":"teacher","status":200,"request":{"$ref":"#/components/schemas/AgentInput"},"response":{"$ref":"#/components/schemas/Agent"},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
func (s *Service) SaveAgent(w http.ResponseWriter, r *http.Request) {
	u, _ := auth.FromContext(r.Context())
	var in AgentInput
	if !body(w, r, &in) {
		return
	}
	in.Name = strings.TrimSpace(in.Name)
	if in.Name == "" || len([]rune(in.Name)) > 64 || len([]rune(in.Prompt)) > 2000 || len(in.SkillIDs) > 200 || len(in.MaterialIDs) > 1000 {
		fail(w, 400, "名称必填且最多64字，提示词最多2000字，绑定数量超过上限")
		return
	}
	id := pathID(r)
	tx, e := s.DB.BeginTx(r.Context(), nil)
	if e != nil {
		dbFail(w)
		return
	}
	defer tx.Rollback()
	if r.Method == "PUT" {
		var found int64
		e = tx.QueryRow(`SELECT id FROM tutor_agents WHERE id=? AND class_id=? FOR UPDATE`, id, u.ClassID).Scan(&found)
		if e != nil {
			resourceError(w, e)
			return
		}
	}
	for _, x := range []struct {
		table string
		ids   []int64
	}{{"tutor_skills", in.SkillIDs}, {"materials", in.MaterialIDs}} {
		for _, v := range x.ids {
			var found int64
			e = tx.QueryRow(`SELECT id FROM `+x.table+` WHERE id=? AND class_id=?`, v, u.ClassID).Scan(&found)
			if e != nil {
				resourceError(w, e)
				return
			}
		}
	}
	if r.Method == "POST" {
		var res sql.Result
		res, e = tx.Exec(`INSERT INTO tutor_agents(class_id,name,prompt,enabled) VALUES(?,?,?,?)`, u.ClassID, in.Name, in.Prompt, in.Enabled)
		if e == nil {
			id, e = res.LastInsertId()
		}
	} else {
		_, e = tx.Exec(`UPDATE tutor_agents SET name=?,prompt=?,enabled=? WHERE id=? AND class_id=?`, in.Name, in.Prompt, in.Enabled, id, u.ClassID)
	}
	if e != nil {
		if strings.Contains(e.Error(), "Duplicate entry") {
			fail(w, 400, "本班智能体名称已存在")
		} else {
			dbFail(w)
		}
		return
	}
	for _, x := range []struct {
		table, col string
		ids        []int64
	}{{"tutor_agent_skills", "skill_id", in.SkillIDs}, {"tutor_agent_materials", "material_id", in.MaterialIDs}} {
		if _, e = tx.Exec(`DELETE FROM `+x.table+` WHERE agent_id=?`, id); e != nil {
			dbFail(w)
			return
		}
		for _, v := range x.ids {
			if _, e = tx.Exec(`INSERT IGNORE INTO `+x.table+`(agent_id,`+x.col+`) VALUES(?,?)`, id, v); e != nil {
				dbFail(w)
				return
			}
		}
	}
	if e = tx.Commit(); e != nil {
		dbFail(w)
		return
	}
	a, e := s.agent(r.Context(), id, u.ClassID, false)
	if e != nil {
		dbFail(w)
		return
	}
	status := 200
	if r.Method == "POST" {
		status = 201
	}
	jsonResponse(w, status, a)
}
func (s *Service) skills(ctx context.Context, classID, agentID int64) ([]Skill, error) {
	q := `SELECT s.id,s.name,s.trigger_text,s.subject_text,s.description,s.tools_json,s.source_text,s.enabled FROM tutor_skills s WHERE s.class_id=?`
	args := []any{classID}
	if agentID > 0 {
		q += ` AND s.enabled=TRUE AND s.id IN (SELECT skill_id FROM tutor_agent_skills WHERE agent_id=?)`
		args = append(args, agentID)
	}
	q += ` ORDER BY s.id`
	rows, e := s.DB.QueryContext(ctx, q, args...)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	out := []Skill{}
	for rows.Next() {
		var v Skill
		var tools string
		if e = rows.Scan(&v.ID, &v.Name, &v.Trigger, &v.Subject, &v.Description, &tools, &v.Source, &v.Enabled); e != nil {
			return nil, e
		}
		if e = json.Unmarshal([]byte(tools), &v.Tools); e != nil {
			return nil, e
		}
		out = append(out, v)
	}
	return out, rows.Err()
}
// @api {"method":"GET","path":"/api/skills","summary":"列出本班技能","auth":"login","status":200,"request":null,"response":{"type":"array","items":{"$ref":"#/components/schemas/Skill"}},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
func (s *Service) Skills(w http.ResponseWriter, r *http.Request) {
	u, _ := auth.FromContext(r.Context())
	v, e := s.skills(r.Context(), u.ClassID, 0)
	if e != nil {
		dbFail(w)
		return
	}
	jsonResponse(w, 200, v)
}
// @api {"method":"GET","path":"/api/skills/{id}","summary":"读取本班技能文件","auth":"login","status":200,"request":null,"response":{"$ref":"#/components/schemas/Skill"},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
func (s *Service) Skill(w http.ResponseWriter, r *http.Request) {
	u, _ := auth.FromContext(r.Context())
	v, e := s.skills(r.Context(), u.ClassID, 0)
	if e != nil {
		dbFail(w)
		return
	}
	for _, sk := range v {
		if sk.ID == pathID(r) {
			jsonResponse(w, 200, sk)
			return
		}
	}
	missing(w)
}
// @api {"method":"POST","path":"/api/skills","summary":"解析技能文件并创建","auth":"teacher","status":201,"request":{"$ref":"#/components/schemas/SkillInput"},"response":{"$ref":"#/components/schemas/Skill"},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
// @api {"method":"PUT","path":"/api/skills/{id}","summary":"修改技能文件（启用填是或否）","auth":"teacher","status":200,"request":{"$ref":"#/components/schemas/SkillInput"},"response":{"$ref":"#/components/schemas/Skill"},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
// @api {"method":"DELETE","path":"/api/skills/{id}","summary":"删除技能并解除绑定","auth":"teacher","status":204,"request":null,"response":null,"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
func (s *Service) SaveSkill(w http.ResponseWriter, r *http.Request) {
	u, _ := auth.FromContext(r.Context())
	id := pathID(r)
	if r.Method != "POST" {
		var found int64
		if e := s.DB.QueryRowContext(r.Context(), `SELECT id FROM tutor_skills WHERE id=? AND class_id=?`, id, u.ClassID).Scan(&found); e != nil {
			resourceError(w, e)
			return
		}
	}
	if r.Method == "DELETE" {
		if _, e := s.DB.ExecContext(r.Context(), `DELETE FROM tutor_skills WHERE id=? AND class_id=?`, id, u.ClassID); e != nil {
			dbFail(w)
			return
		}
		w.WriteHeader(204)
		return
	}
	var in struct {
		Source string `json:"source_text"`
	}
	if !body(w, r, &in) {
		return
	}
	sk, e := ParseSkill(in.Source)
	if e != nil {
		fail(w, 400, e.Error())
		return
	}
	tools, _ := json.Marshal(sk.Tools)
	if r.Method == "POST" {
		var res sql.Result
		res, e = s.DB.ExecContext(r.Context(), `INSERT INTO tutor_skills(class_id,name,trigger_text,subject_text,description,tools_json,source_text,enabled) VALUES(?,?,?,?,?,?,?,?)`, u.ClassID, sk.Name, sk.Trigger, sk.Subject, sk.Description, string(tools), sk.Source, sk.Enabled)
		if e == nil {
			id, e = res.LastInsertId()
		}
	} else {
		_, e = s.DB.ExecContext(r.Context(), `UPDATE tutor_skills SET name=?,trigger_text=?,subject_text=?,description=?,tools_json=?,source_text=?,enabled=? WHERE id=? AND class_id=?`, sk.Name, sk.Trigger, sk.Subject, sk.Description, string(tools), sk.Source, sk.Enabled, id, u.ClassID)
	}
	if e != nil {
		if strings.Contains(e.Error(), "Duplicate entry") {
			fail(w, 400, "本班技能名称已存在")
		} else {
			dbFail(w)
		}
		return
	}
	sk.ID = id
	status := 200
	if r.Method == "POST" {
		status = 201
	}
	jsonResponse(w, status, sk)
}

type Conversation struct {
	ID        int64  `json:"id"`
	AgentID   int64  `json:"agent_id"`
	AgentName string `json:"agent_name"`
	Title     string `json:"title"`
	Created   string `json:"created_at"`
	Updated   string `json:"updated_at"`
}
type Message struct {
	ID        int64                `json:"id"`
	Role      string               `json:"role"`
	Content   string               `json:"content"`
	Citations []retrieval.Citation `json:"citations"`
	SkillName string               `json:"skill_name"`
	Status    string               `json:"status"`
}

func (s *Service) conversation(ctx context.Context, id int64, u auth.User) (Conversation, error) {
	var c Conversation
	e := s.DB.QueryRowContext(ctx, `SELECT c.id,c.agent_id,a.name,c.title,c.created_at,c.updated_at FROM conversations c JOIN tutor_agents a ON a.id=c.agent_id WHERE c.id=? AND c.user_id=? AND c.class_id=? AND a.class_id=?`, id, u.ID, u.ClassID, u.ClassID).Scan(&c.ID, &c.AgentID, &c.AgentName, &c.Title, &c.Created, &c.Updated)
	return c, e
}
// @api {"method":"GET","path":"/api/conversations","summary":"列出本人本班会话","auth":"login","status":200,"request":null,"response":{"type":"array","items":{"$ref":"#/components/schemas/Conversation"}},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
func (s *Service) Conversations(w http.ResponseWriter, r *http.Request) {
	u, _ := auth.FromContext(r.Context())
	rows, e := s.DB.QueryContext(r.Context(), `SELECT c.id,c.agent_id,a.name,c.title,c.created_at,c.updated_at FROM conversations c JOIN tutor_agents a ON a.id=c.agent_id WHERE c.user_id=? AND c.class_id=? AND a.class_id=? ORDER BY c.updated_at DESC,c.id DESC`, u.ID, u.ClassID, u.ClassID)
	if e != nil {
		dbFail(w)
		return
	}
	defer rows.Close()
	out := []Conversation{}
	for rows.Next() {
		var c Conversation
		if e = rows.Scan(&c.ID, &c.AgentID, &c.AgentName, &c.Title, &c.Created, &c.Updated); e != nil {
			dbFail(w)
			return
		}
		out = append(out, c)
	}
	if rows.Err() != nil {
		dbFail(w)
		return
	}
	jsonResponse(w, 200, out)
}
// @api {"method":"POST","path":"/api/conversations","summary":"选择本班启用智能体创建私人会话","auth":"login","status":201,"request":{"type":"object","properties":{"agent_id":{"type":"integer","format":"int64"}},"required":["agent_id"]},"response":{"$ref":"#/components/schemas/Conversation"},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
func (s *Service) CreateConversation(w http.ResponseWriter, r *http.Request) {
	u, _ := auth.FromContext(r.Context())
	var in struct {
		AgentID int64 `json:"agent_id"`
	}
	if !body(w, r, &in) {
		return
	}
	var n int
	if e := s.DB.QueryRowContext(r.Context(), `SELECT COUNT(*) FROM tutor_agents WHERE class_id=? AND enabled=TRUE`, u.ClassID).Scan(&n); e != nil {
		dbFail(w)
		return
	}
	if n == 0 {
		fail(w, 400, "本班暂无可用的智能体")
		return
	}
	if _, e := s.agent(r.Context(), in.AgentID, u.ClassID, true); e != nil {
		resourceError(w, e)
		return
	}
	res, e := s.DB.ExecContext(r.Context(), `INSERT INTO conversations(class_id,user_id,agent_id) VALUES(?,?,?)`, u.ClassID, u.ID, in.AgentID)
	if e != nil {
		dbFail(w)
		return
	}
	id, e := res.LastInsertId()
	if e != nil {
		dbFail(w)
		return
	}
	c, e := s.conversation(r.Context(), id, u)
	if e != nil {
		dbFail(w)
		return
	}
	jsonResponse(w, 201, c)
}
func (s *Service) messages(ctx context.Context, id int64, recent bool) ([]Message, error) {
	q := `SELECT id,role,content,citations_json,skill_name,status FROM messages WHERE conversation_id=? ORDER BY id`
	if recent {
		q += ` DESC LIMIT 6`
	}
	rows, e := s.DB.QueryContext(ctx, q, id)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	out := []Message{}
	for rows.Next() {
		var m Message
		var cites string
		if e = rows.Scan(&m.ID, &m.Role, &m.Content, &cites, &m.SkillName, &m.Status); e != nil {
			return nil, e
		}
		if e = json.Unmarshal([]byte(cites), &m.Citations); e != nil {
			return nil, e
		}
		out = append(out, m)
	}
	if recent {
		for i, j := 0, len(out)-1; i < j; i, j = i+1, j-1 {
			out[i], out[j] = out[j], out[i]
		}
	}
	return out, rows.Err()
}
// @api {"method":"GET","path":"/api/conversations/{id}","summary":"读取本人会话和全部消息","auth":"login","status":200,"request":null,"response":{"type":"object","properties":{"conversation":{"$ref":"#/components/schemas/Conversation"},"messages":{"type":"array","items":{"$ref":"#/components/schemas/Message"}}}},"errors":{"400":"参数非法或本班名称重复","401":"未登录","403":"仅教师可写","404":"资源不存在（他班与不存在同形）","503":"服务暂时不可用"}}
func (s *Service) Conversation(w http.ResponseWriter, r *http.Request) {
	u, _ := auth.FromContext(r.Context())
	c, e := s.conversation(r.Context(), pathID(r), u)
	if e != nil {
		resourceError(w, e)
		return
	}
	m, e := s.messages(r.Context(), c.ID, false)
	if e != nil {
		dbFail(w)
		return
	}
	jsonResponse(w, 200, map[string]any{"conversation": c, "messages": m})
}
