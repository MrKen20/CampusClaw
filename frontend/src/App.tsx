import { useCallback, useEffect, useState } from 'react'
import { api, setUnauthorizedHandler, type Me } from './api'
import LoginPage from './pages/Login'
import MaterialsPage from './pages/Materials'
import AskPage from './pages/Ask'
import TutorPage from './pages/Tutor'
import { ToastProvider } from './components/Toast'

export type Theme = 'light' | 'dark'
type Page = 'materials' | 'ask' | 'tutor'

export default function App() {
  // 身份只来自 /api/me；本地仅持久化不透明 token（localStorage），不持久化角色（spec R9 刷新后身份恢复）。
  const [me, setMe] = useState<Me | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState<Page>('materials')
  // 检索/问答命中后跳转到材料页并打开详情（沿用第 3 课鉴权与 404 语义）
  const [materialJump, setMaterialJump] = useState<number | null>(null)
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem('theme') as Theme) || 'light',
  )

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('theme', theme)
  }, [theme])

  const handleUnauthorized = useCallback(() => setMe(null), [])
  useEffect(() => {
    setUnauthorizedHandler(handleUnauthorized)
    window.addEventListener('tutor-unauthorized', handleUnauthorized)
    return () => window.removeEventListener('tutor-unauthorized', handleUnauthorized)
  }, [handleUnauthorized])

  useEffect(() => {
    api
      .me()
      .then(setMe)
      .catch(() => setMe(null))
      .finally(() => setLoading(false))
  }, [])

  const openMaterial = useCallback((id: number) => {
    setMaterialJump(id)
    setPage('materials')
  }, [])

  if (loading) return null

  return (
    <ToastProvider>
      {me ? (
        <>
<nav className="app-nav"><button onClick={()=>setPage('materials')}>材料</button><button onClick={()=>setPage('ask')}>知识问答</button><button className={page==='tutor'?'primary':''} onClick={()=>setPage('tutor')}>智能体对话</button><span className="spacer"/><span>{me.username} · {me.class_name}</span><button onClick={async()=>{await api.logout().catch(()=>{});setMe(null)}}>登出</button></nav>
<div hidden={page!=='tutor'}><TutorPage me={me} onOpenMaterial={openMaterial}/></div>
{page === 'materials' ? (
          <MaterialsPage
            me={me}
            theme={theme}
            onToggleTheme={() => setTheme((t) => (t === 'light' ? 'dark' : 'light'))}
            onLogout={async () => {
              await api.logout().catch(() => {})
              setMe(null)
            }}
            onOpenAsk={() => setPage('ask')}
            jumpToDetail={materialJump}
            onJumpConsumed={() => setMaterialJump(null)}
          />
        ) : page === 'ask' ? (
          <AskPage
            me={me}
            theme={theme}
            onToggleTheme={() => setTheme((t) => (t === 'light' ? 'dark' : 'light'))}
            onLogout={async () => {
              await api.logout().catch(() => {})
              setMe(null)
            }}
            onOpenMaterials={() => setPage('materials')}
            onOpenMaterial={openMaterial}
          />
        ) : null}
</>
      ) : (
        <LoginPage onSuccess={setMe} />
      )}
    </ToastProvider>
  )
}
