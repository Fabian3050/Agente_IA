import { useState } from "react";
import {
    LayoutDashboard, FileText, Globe, BookOpen, Bot, CheckSquare,
    ClipboardList, BarChart2, Settings, User, Bell, Search,
    TrendingUp, AlertCircle, CheckCircle, Clock, Zap, Filter,
    ChevronRight, ChevronDown, ExternalLink, RefreshCw, Download,
    Eye, Edit3, X, ThumbsUp, AlertTriangle, Activity, Database,
    FileSearch, Cpu, Shield, Menu, ArrowUpRight, Circle, LogIn, ArrowRight, Lock, ShieldCheck,
    Users, UserPlus, UserCheck, UserX, Key, Plus
} from "lucide-react";
import {
    PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Legend
} from "recharts";

// ─── Types ───────────────────────────────────────────────────────────────────
type Page =
    | "dashboard"
    | "monitoreo"
    | "recuperacion"
    | "analisis"
    | "validacion"
    | "aprobacion"
    | "auditoria"
    | "reportes"
    | "usuarios"
    | "configuracion"
    | "perfil";

// ─── Data ────────────────────────────────────────────────────────────────────
const donutData = [
    { name: "Abstract", value: 42, color: "#00aea7" },
    { name: "Palabras clave", value: 26, color: "#F57C00" },
    { name: "Área OCDE", value: 26, color: "#7B1FA2" },
    { name: "Área ODS", value: 12, color: "#2E7D32" },
    { name: "Derechos de acceso", value: 4, color: "#E53935" },
];

const barData = [
    { day: "Lun", value: 187 },
    { day: "Mar", value: 243 },
    { day: "Mié", value: 198 },
    { day: "Jue", value: 312 },
    { day: "Vie", value: 276 },
    { day: "Sáb", value: 94 },
    { day: "Dom", value: 41 },
];

const monitoreoData = [
    { id: "13458", title: "Machine Learning for Biodiversity", campo: "Abstract", fecha: "2024-06-28", prioridad: "Alta", estado: "Pendiente", completitud: 65, completitudPre: 40, coleccion: "Artículos Científicos", comunidad: "Facultad de Ciencia", autor: "Fabián Escobedo", doi: "10.1016/j.envsoft.2024.105892" },
    { id: "18954", title: "Open Science in Chile", campo: "Keywords", fecha: "2024-06-27", prioridad: "Media", estado: "En proceso", completitud: 40, completitudPre: 25, coleccion: "Tesis de Postgrado", comunidad: "Facultad de Ingeniería", autor: "María González", doi: "10.1038/s41586-024-07123-x" },
    { id: "22103", title: "Genomic Sequencing Methods", campo: "DOI", fecha: "2024-06-27", prioridad: "Alta", estado: "Pendiente", completitud: 80, completitudPre: 60, coleccion: "Revistas USACH", comunidad: "Facultad de Química", autor: "Roberto Muñoz", doi: "10.1016/j.genomics.2024.110234" },
    { id: "09871", title: "Climate Change Adaptation", campo: "Materia", fecha: "2024-06-26", prioridad: "Baja", estado: "Completado", completitud: 95, completitudPre: 70, coleccion: "Artículos Científicos", comunidad: "Facultad de Ingeniería", autor: "Patricia Soto", doi: "10.1007/s10584-024-03712-8" },
    //{ id: "31204", title: "Nanotechnology Applications", campo: "Abstract", fecha: "2024-06-26", prioridad: "Alta", estado: "En proceso", completitud: 30, completitudPre: 15, coleccion: "Documentos de Trabajo", comunidad: "Facultad de Ciencia", autor: "Carlos Fuentes", doi: "10.1021/acsnano.4c01234" },
    //{ id: "14729", title: "Urban Mobility Patterns", campo: "Derechos", fecha: "2024-06-25", prioridad: "Media", estado: "Pendiente", completitud: 50, completitudPre: 30, coleccion: "Tesis de Postgrado", comunidad: "Facultad de Tecnológica", autor: "Mónica Araya", doi: "10.1016/j.jtrangeo.2024.103812" },
    //{ id: "28331", title: "Quantum Computing Basics", campo: "Keywords", fecha: "2024-06-25", prioridad: "Baja", estado: "Completado", completitud: 90, completitudPre: 65, coleccion: "Revistas USACH", comunidad: "Facultad de Ciencia", autor: "Fabián Escobedo", doi: "10.1103/PhysRevLett.132.120401" },
];

const apiSources = [
    { name: "OpenAlex", status: "Conectado", latency: "142ms", queries: 1920, recovered: 1847, availability: 99.9, lastQuery: "Hace 2 min" },
    { name: "CrossRef", status: "Conectado", latency: "89ms", queries: 1250, recovered: 1203, availability: 99.7, lastQuery: "Hace 5 min" },
    //{ name: "Scopus", status: "Conectado", latency: "201ms", queries: 910, recovered: 876, availability: 98.2, lastQuery: "Hace 8 min" },
    //{ name: "Web of Science", status: "Conectado", latency: "317ms", queries: 580, recovered: 542, availability: 97.8, lastQuery: "Hace 12 min" },
];

const aprobacionData = [
    { registro: "#13458", campo: "Abstract", valor: "This study presents a machine learning framework for biodiversity monitoring...", fuente: "OpenAlex", confianza: 96, responsable: "María González", rol: "Curador" },
    { registro: "#18954", campo: "Palabras clave", valor: "open science; scholarly communication; Chile; repositories", fuente: "Crossref", confianza: 88, responsable: "Roberto Muñoz", rol: "Administrador" },
    { registro: "#22103", campo: "Área OCDE", valor: "106 Biología y Ciencias Biológicas (1.06)", fuente: "WoS", confianza: 99, responsable: "Patricia Soto", rol: "Curador" },
    { registro: "#31204", campo: "Derechos de acceso", valor: "Acceso Abierto (Creative Commons CC BY 4.0)", fuente: "Extracción directa de PDF", confianza: 91, responsable: "Carlos Fuentes", rol: "Administrador" },
];

const recentActivity = [
    { icon: CheckCircle, color: "#00aea7", text: "Abstract recuperado desde OpenAlex", date: "28 jun", time: "09:16", user: "Agente IA" },
    { icon: CheckCircle, color: "#00aea7", text: "DOI validado mediante CrossRef", date: "28 jun", time: "09:14", user: "Agente IA" },
    { icon: CheckCircle, color: "#00aea7", text: "PDF analizado correctamente", date: "28 jun", time: "09:10", user: "Agente IA" },
    { icon: AlertTriangle, color: "#F57C00", text: "Registro #18954 requiere revisión humana", date: "28 jun", time: "08:58", user: "Sistema" },
    { icon: CheckCircle, color: "#00aea7", text: "Metadato aprobado por María González", date: "28 jun", time: "08:45", user: "María González" },
    { icon: CheckCircle, color: "#2E7D32", text: "Registro #09871 listo para ser publicado.", date: "27 jun", time: "17:32", user: "Sistema" },
    { icon: AlertTriangle, color: "#F57C00", text: "Registro #22103 pendiente de validación.", date: "27 jun", time: "16:20", user: "Monitor" },
];

// ─── Helper Components ────────────────────────────────────────────────────────
function Badge({ children, color }: { children: React.ReactNode; color: string }) {
    const styles: Record<string, string> = {
        Alta: "bg-red-50 text-red-700 border border-red-200",
        Media: "bg-amber-50 text-amber-700 border border-amber-200",
        Baja: "bg-blue-50 text-blue-600 border border-blue-200",
        Pendiente: "bg-orange-50 text-orange-700 border border-orange-200",
        "En proceso": "bg-teal-50 text-teal-700 border border-teal-200",
        Completado: "bg-green-50 text-green-700 border border-green-200",
        Conectado: "bg-green-50 text-green-700 border border-green-200",
    };
    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[color] || "bg-gray-50 text-gray-600 border border-gray-200"}`}>
            {children}
        </span>
    );
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
    return (
        <div className={`bg-white rounded-xl border border-black/[0.06] shadow-sm ${className}`}>
            {children}
        </div>
    );
}

function SectionHeader({ title, description }: { title: string; description: string }) {
    return (
        <div className="mb-6">
            <h1 className="text-xl font-semibold text-[#1a2332]">{title}</h1>
            <p className="text-sm text-[#6b7a90] mt-1">{description}</p>
        </div>
    );
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────
const navItems: { key: Page; label: string; icon: React.ElementType }[] = [
    { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { key: "monitoreo", label: "Monitoreo de registros", icon: FileText },
    { key: "analisis", label: "Análisis documental PDF", icon: BookOpen },
    { key: "validacion", label: "Validación de metadatos", icon: ShieldCheck },
    { key: "aprobacion", label: "Aprobación de metadatos", icon: CheckSquare },
    { key: "auditoria", label: "Auditoría", icon: ClipboardList },
    { key: "reportes", label: "Reportes y Estadísticas de Recuperación", icon: BarChart2 },
    { key: "usuarios", label: "Gestión de usuarios", icon: Users },
    { key: "configuracion", label: "Configuración", icon: Settings },
    { key: "perfil", label: "Perfil", icon: User },
];

function Sidebar({ current, onNav, collapsed, onToggle }: {
    current: Page;
    onNav: (p: Page) => void;
    collapsed: boolean;
    onToggle: () => void;
}) {
    return (
        <aside
            className="flex flex-col h-full transition-all duration-300"
            style={{
                width: collapsed ? 64 : 260,
                background: "#00aea7",
                flexShrink: 0,
            }}
        >
            {/* Logo */}
            <div className={`flex items-center gap-3 py-5 border-b border-white/[0.15] ${collapsed ? "justify-center px-2" : "px-4"}`}>
                <button
                    onClick={onToggle}
                    title={collapsed ? "Desplegar sidebar" : "Cerrar sidebar"}
                    className="flex-shrink-0 w-14 h-14 rounded-xl bg-[#00aea7] p-1 flex items-center justify-center cursor-pointer hover:opacity-95 shadow-sm  transition-all overflow-hidden"
                >
                    <img src="/logo-usach.png" alt="Escudo USACH" className="w-full h-full object-contain" />
                </button>
                {!collapsed && (
                    <div className="overflow-hidden">
                        <p className="text-white text-xs font-semibold leading-tight">Agente Inteligente</p>
                        <p className="text-[10px] leading-tight text-white/85">Enriquecimiento de Metadatos</p>
                        <p className="text-[10px] leading-tight text-white/75">DSpace-CRIS | VRIIC</p>
                    </div>
                )}
                {!collapsed && (
                    <button
                        onClick={onToggle}
                        title="Cerrar sidebar"
                        className="ml-auto text-white/70 hover:text-white transition-colors cursor-pointer"
                    >
                        <Menu size={16} />
                    </button>
                )}
            </div>

            {/* Nav */}
            <nav className="flex-1 py-3 overflow-y-auto">
                {navItems.map(({ key, label, icon: Icon }) => {
                    const active = current === key;
                    return (
                        <button
                            key={key}
                            onClick={() => onNav(key)}
                            title={collapsed ? label : undefined}
                            className={`w-full flex items-center gap-3 py-2.5 text-left transition-all duration-150 group ${collapsed ? "justify-center px-2" : "px-4"
                                } ${active ? "bg-[#00968f]" : "hover:bg-[#00968f]"}`}
                            style={{
                                borderLeft: active ? "3px solid #ffffff" : "3px solid transparent",
                            }}
                        >
                            <Icon
                                size={18}
                                style={{ color: active ? "#ffffff" : "rgba(255, 255, 255, 0.85)", flexShrink: 0 }}
                            />
                            {!collapsed && (
                                <span
                                    className="text-sm font-medium truncate group-hover:text-white transition-colors"
                                    style={{ color: active ? "#ffffff" : "rgba(255, 255, 255, 0.85)" }}
                                >
                                    {label}
                                </span>
                            )}
                        </button>
                    );
                })}
            </nav>

            {/* Footer */}
            {!collapsed && (
                <div className="px-4 py-4 border-t border-white/[0.15]">
                    <p className="text-[10px] text-white/75">USACH · VRIIC</p>
                </div>
            )}
        </aside>
    );
}

// ─── Header ──────────────────────────────────────────────────────────────────
function Header({ page, onLogout }: { page: Page; onLogout?: () => void }) {
    const [showNotifications, setShowNotifications] = useState(false);
    const meta: Record<Page, { title: string; desc: string }> = {
        dashboard: { title: "Dashboard", desc: "Estadísticas generales del sistema de enriquecimiento de metadatos." },
        monitoreo: { title: "Monitoreo de Registros", desc: "Supervisión de registros incompletos detectados en el repositorio DSpace-CRIS." },
        recuperacion: { title: "Reportes y Estadísticas de Recuperación", desc: "Análisis integral del rendimiento del agente inteligente, consultas y conectividad con fuentes externas." },
        analisis: { title: "Análisis Documental PDF", desc: "Extracción y análisis automatizado de metadatos desde documentos científicos." },
        validacion: { title: "Validación Humana de Metadatos", desc: "Revisión de los metadatos extraídos por el agente para asegurar su calidad y precisión." },
        aprobacion: { title: "Aprobación Humana de Metadatos", desc: "Revisión final y decisión humana para autorizar metadatos validados previamente." },
        auditoria: { title: "Auditoría y Trazabilidad", desc: "Línea temporal completa del proceso de enriquecimiento por registro." },
        reportes: { title: "Reportes y Estadísticas de Recuperación", desc: "Análisis integral del rendimiento del agente inteligente, consultas y conectividad con fuentes externas." },
        usuarios: { title: "Gestión de Usuarios", desc: "Administración, modificación y revocación de roles y permisos de acceso al sistema." },
        configuracion: { title: "Configuración", desc: "Configuración de parámetros del sistema, modelo de IA y conexión con fuentes externas." },
        perfil: { title: "Perfil de Usuario", desc: "Información personal, permisos y preferencias del usuario." },
    };

    return (
        <header className="h-16 bg-white border-b border-black/[0.06] flex items-center px-6 gap-4 flex-shrink-0">
            <div className="flex-1 min-w-0">
                <h1 className="text-base font-semibold text-[#1a2332] leading-tight">{meta[page].title}</h1>
                <p className="text-xs text-[#6b7a90] truncate">{meta[page].desc}</p>
            </div>
            <div className="flex items-center gap-3 relative">
                <button
                    onClick={() => setShowNotifications(!showNotifications)}
                    className="relative p-2 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                    title="Ver notificaciones y alertas del sistema"
                >
                    <Bell size={18} className="text-[#6b7a90]" />
                    <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#F57C00]" />
                </button>

                {showNotifications && (
                    <div className="absolute right-36 top-12 w-80 bg-white rounded-xl shadow-xl border border-gray-100 p-4 z-50 animate-in fade-in zoom-in-95 duration-150">
                        <div className="flex items-center justify-between pb-2 mb-3 border-b border-gray-100">
                            <span className="text-xs font-semibold text-[#1a2332]">Notificaciones del Sistema</span>
                            <span className="text-[10px] font-medium bg-amber-50 text-[#F57C00] px-2 py-0.5 rounded-full">2 pendientes</span>
                        </div>
                        <div className="space-y-3 max-h-64 overflow-y-auto">
                            <div className="p-2.5 rounded-lg bg-amber-50/60 border border-amber-200/60 text-left">
                                <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900 mb-1">
                                    <Clock size={13} className="text-[#F57C00]" />
                                    Revisión Pendiente (Curador / Admin)
                                </div>
                                <p className="text-[11px] text-amber-800 leading-snug">Existen 123 registros con sugerencias del agente IA esperando validación y aprobación en el repositorio.</p>
                            </div>
                            <div className="p-2.5 rounded-lg bg-red-50/60 border border-red-200/60 text-left">
                                <div className="flex items-center gap-1.5 text-xs font-bold text-red-900 mb-1">
                                    <AlertTriangle size={13} className="text-red-600" />
                                    Error en Enriquecimiento
                                </div>
                                <p className="text-[11px] text-red-800 leading-snug">Timeout al consultar Web of Science para el registro #18954. Se generó solicitud de revisión manual.</p>
                            </div>
                        </div>
                    </div>
                )}

                <div className="flex items-center gap-2.5 pl-3 border-l border-gray-100">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold" style={{ background: "#00aea7" }}>
                        AV
                    </div>
                    <div className="hidden sm:block">
                        <p className="text-xs font-medium text-[#1a2332] leading-tight">Administrador VRIIC</p>
                        <p className="text-[11px] text-[#6b7a90] leading-tight">Administrador</p>
                    </div>
                    {onLogout && (
                        <button
                            onClick={onLogout}
                            title="Cerrar sesión"
                            className="p-1.5 ml-1 rounded-lg text-[#6b7a90] hover:text-[#d32f2f] hover:bg-[#ffebee]/80 transition-colors cursor-pointer"
                        >
                            <LogIn size={16} className="rotate-180" />
                        </button>
                    )}
                </div>
            </div>
        </header>
    );
}

// ─── PAGES ───────────────────────────────────────────────────────────────────

// Dashboard
function DashboardPage({ onNav }: { onNav?: (p: Page) => void }) {
    const kpis = [
        { label: "Total registros monitoreados", value: "14.327", icon: Database, color: "#1565C0", bg: "#e3f2fd" },
        { label: "Registros incompletos", value: "1.024", icon: AlertCircle, color: "#F57C00", bg: "#fff3e0" },
        { label: "Metadatos enriquecidos", value: "8.912", icon: CheckCircle, color: "#00aea7", bg: "#e0f7f6" },
        { label: "Pendientes de validación", value: "123", icon: Clock, color: "#7B1FA2", bg: "#f3e5f5" },
        { label: "Porcentaje de completitud", value: "62.2%", icon: TrendingUp, color: "#2E7D32", bg: "#e8f5e9", progress: 62 },
        { label: "Tiempo prom. por registro", value: "1 min 48 seg", icon: Zap, color: "#E53935", bg: "#ffebee" },
    ];

    return (
        <div className="flex gap-6 h-full min-h-0">
            {/* Main content */}
            <div className="flex-1 min-w-0 overflow-y-auto pr-1">
                <SectionHeader title="Dashboard" description="Vista general del sistema de enriquecimiento de metadatos." />

                {/* KPIs */}
                <div className="grid grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
                    {kpis.map((kpi) => {
                        const Icon = kpi.icon;
                        return (
                            <Card key={kpi.label} className="p-4">
                                <div className="flex items-start gap-3">
                                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: kpi.bg }}>
                                        <Icon size={20} style={{ color: kpi.color }} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs text-[#6b7a90] leading-tight mb-1">{kpi.label}</p>
                                        <p className="text-2xl font-semibold" style={{ color: kpi.color }}>{kpi.value}</p>
                                        {kpi.progress && (
                                            <div className="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                <div className="h-full rounded-full" style={{ width: `${kpi.progress}%`, background: kpi.color }} />
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </Card>
                        );
                    })}
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                    <Card className="p-5">
                        <h3 className="text-sm font-semibold text-[#1a2332] mb-4">Distribución de metadatos incompletos</h3>
                        <div className="flex items-center gap-4">
                            <ResponsiveContainer width={160} height={160}>
                                <PieChart>
                                    <Pie data={donutData} cx="50%" cy="50%" innerRadius={50} outerRadius={75} dataKey="value" strokeWidth={0}>
                                        {donutData.map((entry, i) => (
                                            <Cell key={i} fill={entry.color} />
                                        ))}
                                    </Pie>
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="flex flex-col gap-2">
                                {donutData.map((d) => (
                                    <div key={d.name} className="flex items-center gap-2">
                                        <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: d.color }} />
                                        <span className="text-xs text-[#6b7a90]">{d.name}</span>
                                        <span className="text-xs font-semibold text-[#1a2332] ml-auto pl-2">{d.value}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </Card>

                    <Card className="p-5">
                        <h3 className="text-sm font-semibold text-[#1a2332] mb-4">Registros enriquecidos esta semana</h3>
                        <ResponsiveContainer width="100%" height={160}>
                            <BarChart data={barData} barSize={22}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f0f4f8" vertical={false} />
                                <XAxis dataKey="day" tick={{ fontSize: 11, fill: "#6b7a90" }} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fontSize: 11, fill: "#6b7a90" }} axisLine={false} tickLine={false} />
                                <Tooltip
                                    contentStyle={{ border: "1px solid #e8eef4", borderRadius: 8, fontSize: 12 }}
                                    cursor={{ fill: "#f0f9f8" }}
                                />
                                <Bar dataKey="value" fill="#00aea7" radius={[4, 4, 0, 0]} name="Registros" />
                            </BarChart>
                        </ResponsiveContainer>
                    </Card>
                </div>
            </div>

            {/* Recent Activity Panel */}
            <aside className="w-72 flex-shrink-0 overflow-y-auto">
                <Card className="p-4 h-full">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-semibold text-[#1a2332]">Actividad reciente</h3>
                        <span className="text-xs text-[#00aea7] font-medium cursor-pointer hover:underline">Ver todo</span>
                    </div>
                    <div className="flex flex-col gap-0">
                        {recentActivity.map((item, i) => {
                            const Icon = item.icon;
                            return (
                                <div key={i} className="flex gap-3 py-3 border-b border-gray-50 last:border-0">
                                    <Icon size={15} style={{ color: item.color, flexShrink: 0, marginTop: 1 }} />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs text-[#1a2332] leading-snug">{item.text}</p>
                                        <div className="flex items-center gap-1.5 mt-1">
                                            <span className="text-[11px] text-[#6b7a90]">{item.date}</span>
                                            <Circle size={3} className="text-[#6b7a90]" fill="currentColor" />
                                            <span className="text-[11px] text-[#6b7a90]">{item.time}</span>
                                            <Circle size={3} className="text-[#6b7a90]" fill="currentColor" />
                                            <span className="text-[11px] text-[#6b7a90] truncate">{item.user}</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </Card>
            </aside>
        </div>
    );
}

// Módulo 1 — Monitoreo
function MonitoreoPage() {
    const [search, setSearch] = useState("");
    const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
    const [statusDropdownOpen, setStatusDropdownOpen] = useState(false);
    const [selectedRecord, setSelectedRecord] = useState<typeof monitoreoData[0] | null>(null);

    const filtered = monitoreoData.filter((r) => {
        const matchSearch =
            r.title.toLowerCase().includes(search.toLowerCase()) ||
            r.id.includes(search) ||
            (r.coleccion && r.coleccion.toLowerCase().includes(search.toLowerCase())) ||
            (r.comunidad && r.comunidad.toLowerCase().includes(search.toLowerCase())) ||
            (r.autor && r.autor.toLowerCase().includes(search.toLowerCase())) ||
            (r.doi && r.doi.toLowerCase().includes(search.toLowerCase())) ||
            r.fecha.includes(search);
        const matchFilter = selectedStatuses.length === 0 || selectedStatuses.includes(r.estado);
        return matchSearch && matchFilter;
    });

    return (
        <div className="h-full overflow-y-auto">
            <SectionHeader title="Monitoreo de Registros Incompletos" description="Registros detectados con campos de metadatos faltantes o incompletos en DSpace-CRIS." />

            {/* Stats bar */}
            <div className="flex gap-4 mb-6">
                {[
                    { label: "Total detectados", value: "1.024", color: "#F57C00" },
                    { label: "Pendientes", value: "312", color: "#d32f2f" },
                    { label: "En proceso", value: "187", color: "#00aea7" },
                    { label: "Completados", value: "94", color: "#2E7D32" },
                ].map((s) => (
                    <Card key={s.label} className="flex-1 px-4 py-3">
                        <p className="text-[11px] text-[#6b7a90] mb-1">{s.label}</p>
                        <p className="text-xl font-semibold" style={{ color: s.color }}>{s.value}</p>
                    </Card>
                ))}
            </div>

            <Card>
                {/* Toolbar */}
                <div className="flex items-center gap-3 p-4 border-b border-gray-50">
                    <div className="relative flex-1 max-w-md">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7a90]" />
                        <input
                            type="text"
                            placeholder="Buscar por colección, comunidad, autor, DOI o fecha..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
                        />
                    </div>
                    <div className="flex gap-1.5 ml-auto">
                        <button
                            onClick={() => alert("Ejecutando agente IA de enriquecimiento sobre los 312 registros pendientes...")}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white rounded-lg shadow-2xs hover:opacity-95 transition-all cursor-pointer"
                            style={{ background: "#00aea7" }}
                        >
                            <Zap size={13} /> Ejecutar todos los pendientes
                        </button>
                        <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-200 rounded-lg text-[#6b7a90] hover:bg-gray-50">
                            <Download size={13} />
                            Exportar
                        </button>
                    </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-50">
                                {["ID", "Título / DOI", "Comunidad", "Campo faltante", "Completitud", "Estado", "Acción"].map((h) => {
                                    if (h === "Estado") {
                                        return (
                                            <th key={h} className="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide relative select-none">
                                                <div
                                                    className="flex items-center gap-1.5 cursor-pointer hover:text-[#1a2332] transition-colors inline-flex py-1"
                                                    onClick={() => setStatusDropdownOpen(!statusDropdownOpen)}
                                                >
                                                    <span>Estado</span>
                                                    <Filter size={13} className={selectedStatuses.length > 0 ? "text-[#00aea7]" : "text-[#6b7a90]"} />
                                                    {selectedStatuses.length > 0 && (
                                                        <span className="bg-[#00aea7] text-white rounded-full px-1.5 py-0.2 text-[9px] font-bold">
                                                            {selectedStatuses.length}
                                                        </span>
                                                    )}
                                                    <ChevronDown size={13} className={`text-[#6b7a90] transition-transform ${statusDropdownOpen ? "rotate-180" : ""}`} />
                                                </div>

                                                {statusDropdownOpen && (
                                                    <>
                                                        <div className="fixed inset-0 z-20" onClick={() => setStatusDropdownOpen(false)} />
                                                        <div className="absolute left-0 mt-1 w-52 bg-white rounded-xl shadow-xl border border-gray-100 p-2.5 z-30 font-sans normal-case">
                                                            <div className="text-[10px] font-bold text-[#6b7a90] uppercase px-2 py-1 flex items-center justify-between border-b border-gray-50 mb-1.5">
                                                                <span>Filtrar por estado</span>
                                                                {selectedStatuses.length > 0 && (
                                                                    <button
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            setSelectedStatuses([]);
                                                                        }}
                                                                        className="text-[10px] text-[#00aea7] hover:underline normal-case font-semibold cursor-pointer"
                                                                    >
                                                                        Limpiar todo
                                                                    </button>
                                                                )}
                                                            </div>
                                                            <div className="space-y-1 py-0.5">
                                                                {["Pendiente", "En proceso", "Completado"].map((opt) => {
                                                                    const isSelected = selectedStatuses.includes(opt);
                                                                    return (
                                                                        <label
                                                                            key={opt}
                                                                            onClick={(e) => e.stopPropagation()}
                                                                            className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer text-xs font-medium text-slate-700 select-none transition-colors"
                                                                        >
                                                                            <input
                                                                                type="checkbox"
                                                                                checked={isSelected}
                                                                                onChange={() => {
                                                                                    if (isSelected) {
                                                                                        setSelectedStatuses(selectedStatuses.filter((s) => s !== opt));
                                                                                    } else {
                                                                                        setSelectedStatuses([...selectedStatuses, opt]);
                                                                                    }
                                                                                }}
                                                                                className="rounded border-gray-300 text-[#00aea7] focus:ring-[#00aea7] w-3.5 h-3.5 accent-[#00aea7] cursor-pointer"
                                                                            />
                                                                            <span className="flex-1">{opt}</span>
                                                                        </label>
                                                                    );
                                                                })}
                                                            </div>
                                                        </div>
                                                    </>
                                                )}
                                            </th>
                                        );
                                    }
                                    return (
                                        <th key={h} className="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide">
                                            {h}
                                        </th>
                                    );
                                })}
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((row, i) => (
                                <tr key={row.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                                    <td className="px-4 py-3.5 text-xs font-mono font-medium text-[#1565C0]">#{row.id}</td>
                                    <td className="px-4 py-3.5 max-w-[200px]">
                                        <p className="text-xs font-medium text-[#1a2332] truncate">{row.title}</p>
                                        <p className="text-[10px] font-mono text-[#6b7a90] truncate">DOI: {row.doi || "N/A"}</p>
                                    </td>
                                    <td className="px-4 py-3.5 max-w-[170px]">
                                        <p className="text-xs text-[#1a2332] truncate">{row.comunidad}</p>
                                        {/*<p className="text-[10px] text-[#6b7a90] truncate">{row.coleccion}</p>*/}
                                    </td>
                                    <td className="px-4 py-3.5">
                                        <span className="text-xs font-medium px-2 py-0.5 bg-blue-50 text-blue-700 rounded">{row.campo}</span>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                <div className="h-full rounded-full transition-all" style={{ width: `${row.completitud || 50}%`, background: (row.completitud || 50) >= 80 ? "#2E7D32" : (row.completitud || 50) >= 50 ? "#00aea7" : "#F57C00" }} />
                                            </div>
                                            <span className="text-xs font-bold" style={{ color: (row.completitud || 50) >= 80 ? "#2E7D32" : (row.completitud || 50) >= 50 ? "#00aea7" : "#F57C00" }}>{row.completitud || 50}%</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3.5"><Badge color={row.estado}>{row.estado}</Badge></td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <div className="flex items-center gap-1.5">
                                            <button
                                                onClick={() => setSelectedRecord(row)}
                                                className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-[#00aea7] border border-[#00aea7]/30 rounded-lg hover:bg-[#00aea7]/5 transition-colors cursor-pointer"
                                            >
                                                <Eye size={12} /> Ver
                                            </button>
                                            <button
                                                onClick={() => alert(`Iniciando enriquecimiento individual con agente IA para el registro #${row.id}...`)}
                                                title="Ejecutar agente sobre este único registro"
                                                className="p-1.5 text-xs font-medium text-[#1565C0] hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                                            >
                                                <Zap size={14} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="px-4 py-3 border-t border-gray-50 flex items-center justify-between">
                    <p className="text-xs text-[#6b7a90]">Mostrando {filtered.length} de {monitoreoData.length} registros</p>
                    <div className="flex gap-1">
                        {[1, 2, 3].map((p) => (
                            <button key={p} className="w-7 h-7 text-xs rounded-lg flex items-center justify-center transition-all"
                                style={{ background: p === 1 ? "#00aea7" : "#f0f4f8", color: p === 1 ? "#fff" : "#6b7a90" }}>
                                {p}
                            </button>
                        ))}
                    </div>
                </div>
            </Card>

            {/* Modal de Detalles del Registro */}
            {selectedRecord && (
                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full border border-gray-100 overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
                        {/* Modal Header */}
                        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-slate-50/50">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-[#00aea7]/10 flex items-center justify-center text-[#00aea7] font-mono font-bold text-sm">
                                    #{selectedRecord.id}
                                </div>
                                <div>
                                    <h3 className="text-base font-semibold text-slate-800 flex items-center gap-2">
                                        Detalles del Registro
                                        <Badge color={selectedRecord.estado}>{selectedRecord.estado}</Badge>
                                    </h3>
                                    <p className="text-xs text-slate-500">Repositorio Institucional DSpace-CRIS USACH</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setSelectedRecord(null)}
                                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-6 overflow-y-auto space-y-6">
                            {/* Título y Metadatos Clave */}
                            <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-100 space-y-3">
                                <div>
                                    <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">Título Científico</span>
                                    <p className="text-sm font-semibold text-slate-800 leading-snug">{selectedRecord.title}</p>
                                </div>
                                <div className="grid grid-cols-3 gap-4 pt-2 border-t border-slate-200/60">
                                    <div>
                                        <span className="text-[11px] font-semibold text-slate-400 block">Identificador</span>
                                        <span className="text-xs font-mono text-blue-600">oai:dspace:20.500/{selectedRecord.id}</span>
                                    </div>
                                    <div>
                                        <span className="text-[11px] font-semibold text-slate-400 block">Fecha Detección</span>
                                        <span className="text-xs font-medium text-slate-700">{selectedRecord.fecha}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Alerta de Metadato Faltante / Incompleto */}
                            <div className="rounded-xl p-4 border bg-amber-50/60 border-amber-200/80 flex gap-3.5">
                                <div className="w-9 h-9 rounded-lg bg-amber-500/10 text-amber-600 flex items-center justify-center shrink-0 mt-0.5">
                                    <AlertTriangle size={18} />
                                </div>
                                <div className="space-y-1">
                                    <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wide flex items-center gap-2">
                                        Campo Faltante Detectado: <span className="bg-amber-100 px-2 py-0.5 rounded text-amber-800 font-mono">{selectedRecord.campo}</span>
                                    </h4>
                                    <p className="text-xs text-amber-800/90 leading-relaxed">
                                        {selectedRecord.campo === "Abstract" && "El resumen o abstract original no se encuentra indexado en el registro XML del repositorio DSpace o contiene menos caracteres de los requeridos por el estándar mínimo de indexación."}
                                        {selectedRecord.campo === "Keywords" && "El registro carece de palabras clave normalizadas bajo vocabularios controlados o tesauros internacionales (ej. Tesauro UNESCO, OECD, IEEE)."}
                                        {selectedRecord.campo === "DOI" && "No se detectó un identificador de objeto digital (DOI) en los metadatos bibliográficos exportados desde el repositorio institucional."}
                                        {selectedRecord.campo === "Materia" && "La clasificación por disciplina científica (Áreas de Investigación OCDE u ODS) no se encuentra en el repositorio."}
                                        {selectedRecord.campo === "Derechos" && "Faltan especificaciones de licencia de acceso abierto (Creative Commons) o declaración de derechos de autor interoperables."}
                                        {!["Abstract", "Keywords", "DOI", "Materia", "Derechos"].includes(selectedRecord.campo) && `El campo de metadatos "${selectedRecord.campo}" presenta anomalías o no ha sido completado en la ficha original del repositorio.`}
                                    </p>
                                </div>
                            </div>

                            {/* Estado en Pipeline */}
                            <div className="space-y-2">
                                <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Completitud del campo en el repositorio</h4>
                                <div className="flex items-center justify-between text-xs p-3 rounded-lg bg-slate-50 border border-slate-100 font-medium text-slate-600">
                                    <span className="flex items-center gap-2">
                                        <Activity size={14} className="text-[#00aea7]" />
                                        Sincronización y completitud
                                    </span>
                                    <span className="text-emerald-600 font-semibold flex items-center gap-1">
                                        <CheckCircle size={13} /> Pre-enriquecimiento: {selectedRecord.completitudPre || 40}% a Actual: {selectedRecord.completitud || 65}%
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Modal Footer */}
                        <div className="px-6 py-4 border-t border-gray-100 bg-slate-50/50 flex items-center justify-between gap-3">
                            <span className="text-xs text-slate-400">
                                Última revisión del monitor: Hoy
                            </span>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setSelectedRecord(null)}
                                    className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors"
                                >
                                    Cerrar
                                </button>
                                <button
                                    onClick={() => {
                                        alert(`Enriquecimiento individual en ejecución para el registro #${selectedRecord.id}...`);
                                        setSelectedRecord(null);
                                    }}
                                    className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-[#00aea7] hover:bg-[#009b95] rounded-xl shadow-sm shadow-[#00aea7]/20 transition-all cursor-pointer"
                                >
                                    <Zap size={13} />
                                    Ejecutar Recuperación IA
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Módulo 3 — Análisis PDF / Análisis Documental PDF
function AnalisisPage() {
    const [selectedItem, setSelectedItem] = useState<any | null>(null);
    const [approvedIds, setApprovedIds] = useState<Record<string, boolean>>({});
    const [searchTerm, setSearchTerm] = useState("");

    const pdfRecords = [
        {
            id: "13458",
            title: "Machine Learning for Biodiversity in Andean Ecosystems",
            campo: "Áreas ODS",
            documento: "paper_2024_biodiversity.pdf",
            doi: "10.1016/j.envsoft.2024.105892",
            confianza: 96,
            metadatoExtraido: "ODS 15: Vida de ecosistemas terrestres. Extracción verificada de la sección 'Impact and Sustainability' (Página 11).",
            pags: "12 págs",
            tamaño: "2.4 MB"
        },
        {
            id: "18954",
            title: "Open Science Infrastructure and Policy Frameworks in Chile",
            campo: "Derechos de acceso",
            documento: "open_science_chile_report.pdf",
            doi: "10.1038/s41586-024-07123-x",
            confianza: 88,
            metadatoExtraido: "Acceso Abierto — Creative Commons Atribución 4.0 Internacional (CC BY 4.0). Declarado explícitamente en pie de página (Página 2).",
            pags: "24 págs",
            tamaño: "4.1 MB"
        },
        {
            id: "22103",
            title: "Genomic Sequencing Methods for Marine Microorganisms",
            campo: "Área OCDE",
            documento: "marine_genomics_study.pdf",
            doi: "10.1016/j.genomics.2024.110234",
            confianza: 94,
            metadatoExtraido: "106 Biología y Ciencias Biológicas (1.06). Clasificado algorítmicamente mediante análisis semántico del texto completo.",
            pags: "18 págs",
            tamaño: "3.7 MB"
        }/*,
    {
      id: "31204",
      title: "Nanotechnology Applications in Photovoltaic Solar Cells",
      campo: "Abstract",
      documento: "solar_nanotech_draft.pdf",
      doi: "10.1021/acsnano.4c01234",
      confianza: 91,
      metadatoExtraido: "Nanotechnology applications in biomedical engineering and photovoltaic solar cells have shown unprecedented efficiency gains. This study investigates novel perovskite structures...",
      pags: "15 págs",
      tamaño: "1.9 MB"
    },
    {/
      id: "14729",
      title: "Urban Mobility Patterns in Santiago Metropolitan Area",
      campo: "Palabras clave",
      documento: "urban_mobility_santiago.pdf",
      doi: "10.1016/j.jtrangeo.2024.103812",
      confianza: 98,
      metadatoExtraido: "movilidad urbana; transporte público; área metropolitana; Santiago; planificación urbana; sostenibilidad",
      pags: "20 págs",
      tamaño: "5.2 MB"
    }*/
    ];

    const filtered = pdfRecords.filter(r =>
        r.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.id.includes(searchTerm) ||
        r.documento.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.campo.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="h-full overflow-y-auto">
            <SectionHeader title="Análisis Documental PDF" description="Listado de registros científicos procesados y enriquecidos mediante herramientas de extracción directa de PDF con OCR e IA." />

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <Card className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-semibold text-[#6b7a90] uppercase">Archivos Procesados</span>
                        <div className="w-8 h-8 rounded-lg bg-teal-50 text-[#00aea7] flex items-center justify-center"><FileText size={16} /></div>
                    </div>
                    <p className="text-xl font-bold text-[#1a2332]">5 <span className="text-xs font-normal text-[#6b7a90]">documentos</span></p>
                    <p className="text-[10px] text-[#00aea7] font-medium mt-0.5">OCR UTF-8 normalizado</p>
                </Card>
                <Card className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-semibold text-[#6b7a90] uppercase">Confianza Promedio</span>
                        <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center"><CheckCircle size={16} /></div>
                    </div>
                    <p className="text-xl font-bold text-[#1a2332]">93.4%</p>
                    <p className="text-[10px] text-emerald-600 font-medium mt-0.5">Alta precisión en extracción</p>
                </Card>
                <Card className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-semibold text-[#6b7a90] uppercase">DOIs Identificados</span>
                        <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center"><Globe size={16} /></div>
                    </div>
                    <p className="text-xl font-bold text-[#1a2332]">100%</p>
                    <p className="text-[10px] text-blue-600 font-medium mt-0.5">Enlaces resueltos exitosamente</p>
                </Card>
                <Card className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-semibold text-[#6b7a90] uppercase">Extracciones Aprobadas</span>
                        <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center"><Zap size={16} /></div>
                    </div>
                    <p className="text-xl font-bold text-purple-700">{Object.keys(approvedIds).length} <span className="text-xs font-normal text-[#6b7a90]">de 5</span></p>
                    <p className="text-[10px] text-purple-600 font-medium mt-0.5">Listos para aprobación</p>
                </Card>
            </div>

            <Card>
                <div className="p-4 border-b border-gray-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="relative flex-1 max-w-xs">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7a90]" />
                        <input
                            type="text"
                            placeholder="Buscar por ID, título o archivo..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => {
                                const all: Record<string, boolean> = {};
                                pdfRecords.forEach(r => { all[r.id] = true; });
                                setApprovedIds(all);
                                alert("¡Todas las extracciones PDF han sido aprobadas!");
                            }}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-[#00aea7] rounded-lg shadow-2xs hover:opacity-95 transition-all cursor-pointer"
                        >
                            <CheckCircle size={13} /> Validar todas las extracciones
                        </button>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-50 bg-slate-50/50">
                                {["ID & Título", "Metadato procesado", "Documento", "DOI", "Confianza IA", "Acciones"].map((h) => (
                                    <th key={h} className="text-left px-4 py-3.5 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide whitespace-nowrap">
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((row) => (
                                <tr key={row.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                                    <td className="px-4 py-3.5 max-w-[220px]">
                                        <span className="text-xs font-mono font-bold text-[#1565C0]">#{row.id}</span>
                                        <p className="text-xs font-medium text-[#1a2332] truncate mt-0.5" title={row.title}>{row.title}</p>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <span className="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md border border-blue-100">{row.campo}</span>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <button
                                            onClick={() => alert(`Cargando vista previa del documento original: ${row.documento} (${row.pags})`)}
                                            className="flex items-center gap-1.5 px-2.5 py-1 bg-teal-50/60 hover:bg-teal-50 border border-teal-200/80 rounded-lg text-xs font-medium text-slate-700 transition-colors cursor-pointer"
                                            title="Haz clic para abrir el documento PDF original"
                                        >
                                            <FileText size={14} className="text-[#00aea7] shrink-0" />
                                            <span className="underline decoration-teal-300 font-mono text-[11px]">{row.documento}</span>
                                            <span className="text-[10px] text-slate-400">({row.pags})</span>
                                        </button>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <a
                                            href={`https://doi.org/${row.doi}`}
                                            target="_blank"
                                            rel="noreferrer"
                                            onClick={(e) => { e.preventDefault(); alert(`Resolviendo DOI externo: https://doi.org/${row.doi}`); }}
                                            className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 hover:underline font-mono"
                                            title="Resolver DOI en CrossRef/org"
                                        >
                                            <Globe size={13} className="shrink-0 text-blue-500" />
                                            <span>{row.doi}</span>
                                        </a>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <div className="flex items-center gap-2">
                                            <div className="w-14 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                <div className="h-full rounded-full" style={{ width: `${row.confianza}%`, background: row.confianza >= 90 ? "#00aea7" : "#F57C00" }} />
                                            </div>
                                            <span className="text-xs font-bold" style={{ color: row.confianza >= 90 ? "#2E7D32" : "#F57C00" }}>{row.confianza}%</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <div className="flex items-center gap-1.5">
                                            <button
                                                onClick={() => setApprovedIds(prev => ({ ...prev, [row.id]: !prev[row.id] }))}
                                                className={`flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer shadow-2xs ${approvedIds[row.id]
                                                    ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                                                    : "text-emerald-700 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100"
                                                    }`}
                                                title={approvedIds[row.id] ? "Extracción aprobada por humano" : "Validar la extracción de este metadato"}
                                            >
                                                <CheckCircle size={13} className={approvedIds[row.id] ? "text-emerald-700" : ""} />
                                                {approvedIds[row.id] ? "Validado" : "Validar extracción"}
                                            </button>
                                            <button
                                                onClick={() => setSelectedItem(row)}
                                                className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-[#00aea7] bg-[#00aea7]/10 border border-[#00aea7]/30 rounded-lg hover:bg-[#00aea7]/20 transition-all cursor-pointer shadow-2xs"
                                                title="Visualizar el metadato que fue extraído"
                                            >
                                                <Eye size={13} /> Ver metadato
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {filtered.length === 0 && (
                                <tr>
                                    <td colSpan={6} className="px-4 py-8 text-center text-xs text-slate-400">
                                        No se encontraron documentos PDF procesados que coincidan con la búsqueda.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </Card>

            {/* Modal Visualizar Metadato Extraído */}
            {selectedItem && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in duration-150">
                    <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-150 flex flex-col">
                        <div className="px-6 py-4 border-b border-gray-100 bg-slate-50 flex items-center justify-between">
                            <div className="flex items-center gap-2.5">
                                <div className="w-8 h-8 rounded-lg bg-[#00aea7]/10 text-[#00aea7] flex items-center justify-center font-bold">
                                    <FileText size={18} />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-slate-800">Metadato Extraído desde PDF</h3>
                                    <p className="text-[11px] text-slate-500">Registro #{selectedItem.id} — Documento: {selectedItem.documento}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setSelectedItem(null)}
                                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors cursor-pointer"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3.5 rounded-xl border border-gray-100">
                                <div>
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Campo Procesado</span>
                                    <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100 inline-block mt-1">{selectedItem.campo}</span>
                                </div>
                                <div>
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Confianza OCR/IA</span>
                                    <span className="text-xs font-bold text-emerald-700 mt-1 inline-block">{selectedItem.confianza}%</span>
                                </div>
                                <div className="col-span-2 pt-2 border-t border-gray-200/60">
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Identificador Digital (DOI)</span>
                                    <span className="text-xs font-mono text-slate-700 font-medium block mt-0.5">{selectedItem.doi}</span>
                                </div>
                            </div>

                            <div>
                                <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1.5 flex items-center gap-1">
                                    Valor Extraído del Documento original
                                </span>
                                <div className="bg-emerald-50/60 border border-emerald-200/80 rounded-xl p-4 text-xs text-slate-800 font-medium leading-relaxed shadow-2xs">
                                    {selectedItem.metadatoExtraido}
                                </div>
                            </div>
                        </div>

                        <div className="px-6 py-4 border-t border-gray-100 bg-slate-50/60 flex items-center justify-end gap-2">
                            {!approvedIds[selectedItem.id] && (
                                <button
                                    onClick={() => {
                                        setApprovedIds(prev => ({ ...prev, [selectedItem.id]: true }));
                                        setSelectedItem(null);
                                    }}
                                    className="px-4 py-1.5 rounded-lg text-xs font-semibold text-white bg-[#00aea7] hover:opacity-90 transition-opacity cursor-pointer shadow-xs flex items-center gap-1.5"
                                >
                                    <CheckCircle size={14} /> Validar extracción ahora
                                </button>
                            )}
                            <button
                                onClick={() => setSelectedItem(null)}
                                className="px-4 py-1.5 rounded-lg text-xs font-semibold text-slate-600 bg-white border border-gray-200 hover:bg-gray-50 transition-colors cursor-pointer"
                            >
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Módulo 4 — Validación de metadatos
function ValidacionPage() {
    const [selectedVal, setSelectedVal] = useState<any | null>(null);
    const [filterStatus, setFilterStatus] = useState("Todos");
    const [searchVal, setSearchVal] = useState("");

    const validationRecords = [
        {
            id: "13458",
            title: "Machine Learning for Biodiversity in Andean Ecosystems",
            campo: "Áreas ODS",
            propuestaIA: "ODS 15: Vida de ecosistemas terrestres",
            fuenteHerramienta: "Scopus",
            sintaxis: "Clasificación oficial ODS (Válido)",
            confianza: 96,
            color: "#2E7D32",
            estado: "Apto p/ Aprobación",
            detalle: "La validación algorítmica verificó que la clasificación sugerida pertenece al vocabulario oficial de Objetivos de Desarrollo Sostenible (ODS 15). El esquema de metadatos no presenta conflictos semánticos y es compatible con las directrices institucionales."
        },
        {
            id: "18954",
            title: "Open Science Infrastructure and Policy Frameworks in Chile",
            campo: "Derechos de acceso",
            propuestaIA: "Acceso Abierto (Creative Commons CC BY 4.0)",
            fuenteHerramienta: "Crossref",
            sintaxis: "Licencia CC BY 4.0 (Requiere URI)",
            confianza: 74,
            color: "#F57C00",
            estado: "Anomalía Técnica",
            detalle: "El motor de validación detectó una anomalía técnica: aunque la licencia identificada por el LLM es correcta (CC BY 4.0), el XML del repositorio DSpace local requiere obligatoriamente el enlace URI completo (https://creativecommons.org/licenses/by/4.0/). Requiere normalización antes de pasar a aprobación humana."
        },
        {
            id: "22103",
            title: "Genomic Sequencing Methods for Marine Microorganisms",
            campo: "Área OCDE",
            propuestaIA: "106 Biología y Ciencias Biológicas (1.06)",
            fuenteHerramienta: "WoS",
            sintaxis: "Taxonomía OCDE 3 dígitos (Válido)",
            confianza: 94,
            color: "#2E7D32",
            estado: "Apto p/ Aprobación",
            detalle: "El motor algorítmico clasificó exitosamente la investigación dentro de la taxonomía oficial de Áreas Científico-Tecnológicas de la OCDE (Manual de Frascati), verificando su coherencia con el título y resumen del documento."
        },
        /*
          id: "31204",
          title: "Nanotechnology Applications in Photovoltaic Solar Cells",
          campo: "Abstract",
          propuestaIA: "Abstract estructurado en 3 párrafos (Español e Inglés)",
          fuenteHerramienta: "Extracción directa de PDF",
          sintaxis: "Sin caracteres especiales inválidos",
          confianza: 91,
          color: "#2E7D32",
          estado: "Apto p/ Aprobación",
          detalle: "El análisis de validación de texto constató que el abstract cumple con el mínimo de 150 palabras requerido por las directrices de indexación de SciELO y Latindex. La codificación UTF-8 es limpia y la terminología técnica es coherente."
        },*/
        {
            id: "14729",
            title: "Urban Mobility Patterns in Santiago Metropolitan Area",
            campo: "Palabras clave",
            propuestaIA: "movilidad urbana, transporte público, área metropolitana, planificación urbana",
            fuenteHerramienta: "OpenAlex",
            sintaxis: "Términos normalizados y separados por comas",
            confianza: 98,
            color: "#2E7D32",
            estado: "Apto p/ Aprobación",
            detalle: "El análisis algorítmico contrastó las palabras clave extraídas contra el Tesauro oficial de la UNESCO, confirmando su indización normalizada y coherencia semántica con el área de urbanismo y transporte."
        }
    ];

    const filtered = validationRecords.filter(r => {
        const matchSearch = r.title.toLowerCase().includes(searchVal.toLowerCase()) || r.id.includes(searchVal) || r.campo.toLowerCase().includes(searchVal.toLowerCase());
        const matchFilter = filterStatus === "Todos" || r.estado === filterStatus;
        return matchSearch && matchFilter;
    });

    return (
        <div className="h-full overflow-y-auto">
            <SectionHeader title="Validación de metadatos" description="Asegure la calidad de los metadatos antes de su aprobación final." />

            <Card>
                <div className="p-4 border-b border-gray-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="relative flex-1 max-w-xs">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7a90]" />
                        <input
                            type="text"
                            placeholder="Buscar por ID, título o campo..."
                            value={searchVal}
                            onChange={(e) => setSearchVal(e.target.value)}
                            className="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
                        />
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                        <div className="flex gap-1">
                            {["Todos"].map((f) => (
                                <button
                                    key={f}
                                    onClick={() => setFilterStatus(f)}
                                    className="px-3 py-1.5 text-xs rounded-lg font-medium transition-all cursor-pointer"
                                    style={{
                                        background: filterStatus === f ? "#00aea7" : "#f0f4f8",
                                        color: filterStatus === f ? "#fff" : "#6b7a90",
                                    }}
                                >
                                    {f}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-50 bg-slate-50/50">
                                {["ID & Título", "Campo evaluado", "Fuente", "Confianza IA", "Acciones"].map((h) => (
                                    <th key={h} className="text-left px-4 py-3.5 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide">
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((row) => (
                                <tr key={row.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                                    <td className="px-4 py-3.5 max-w-[220px]">
                                        <span className="text-xs font-mono font-bold text-[#1565C0]">#{row.id}</span>
                                        <p className="text-xs font-medium text-[#1a2332] truncate mt-0.5">{row.title}</p>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <span className="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md border border-blue-100">{row.campo}</span>
                                    </td>
                                    <td className="px-4 py-3.5 text-xs">
                                        <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                                            <Cpu size={14} className="text-[#00aea7] shrink-0" />
                                            <span>{row.fuenteHerramienta}</span>
                                        </div>
                                        <p className="text-[10px] font-mono text-slate-400 mt-0.5">{row.sintaxis}</p>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <div className="flex items-center gap-2">
                                            <div className="w-14 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                <div className="h-full rounded-full" style={{ width: `${row.confianza}%`, background: row.confianza >= 80 ? "#2E7D32" : "#F57C00" }} />
                                            </div>
                                            <span className="text-xs font-bold" style={{ color: row.confianza >= 80 ? "#2E7D32" : "#F57C00" }}>{row.confianza}%</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3.5">
                                        <div className="flex items-center gap-1.5 whitespace-nowrap">
                                            <button
                                                onClick={() => alert(`¡Validación exitosa para el registro #${row.id}!`)}
                                                className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-all cursor-pointer shadow-2xs"
                                                title="Validar el metadato recuperado"
                                            >
                                                <ShieldCheck size={12} /> Validar
                                            </button>
                                            <button
                                                onClick={() => setSelectedVal(row)}
                                                className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-[#00aea7] bg-[#00aea7]/10 border border-[#00aea7]/30 rounded-lg hover:bg-[#00aea7]/20 transition-all cursor-pointer shadow-2xs"
                                                title="Ver el metadato recuperado"
                                            >
                                                <Eye size={12} /> Ver
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </Card>

            {/* Modal de Metadato Recuperado */}
            {selectedVal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in duration-150">
                    <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-150 flex flex-col">
                        <div className="px-6 py-4 border-b border-gray-100 bg-slate-50 flex items-center justify-between">
                            <div className="flex items-center gap-2.5">
                                <div className="w-8 h-8 rounded-lg bg-[#00aea7]/10 text-[#00aea7] flex items-center justify-center font-bold">
                                    <Eye size={18} />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-slate-800">Metadato Recuperado</h3>
                                    <p className="text-[11px] text-slate-500">Valor extraído y procesado automáticamente</p>
                                </div>
                            </div>
                            <button onClick={() => setSelectedVal(null)} className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors cursor-pointer">
                                <X size={18} />
                            </button>
                        </div>

                        <div className="p-6 space-y-4">
                            <div>
                                <span className="text-[10px] font-bold uppercase tracking-wider text-[#00aea7] block mb-1">ID Registro #{selectedVal.id}</span>
                                <h4 className="text-base font-bold text-slate-800 leading-snug">{selectedVal.title}</h4>
                            </div>

                            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60 space-y-3">
                                <div>
                                    <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-1">Campo evaluado</span>
                                    <span className="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md border border-blue-100 inline-block">{selectedVal.campo}</span>
                                </div>

                                <div>
                                    <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-1">Valor propuesto por IA (Metadato)</span>
                                    <div className="p-3 bg-white rounded-lg border border-slate-200 font-mono text-xs text-teal-900 font-medium shadow-2xs break-words">
                                        {selectedVal.propuestaIA}
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3 text-xs">
                                <div className="p-3 rounded-xl border border-gray-100 bg-gray-50/50">
                                    <span className="text-[10px] text-slate-400 font-bold uppercase block mb-0.5">Sintaxis / Formato</span>
                                    <span className="font-mono text-slate-600 text-[11px] truncate block" title={selectedVal.sintaxis}>{selectedVal.sintaxis}</span>
                                </div>
                            </div>
                        </div>

                        <div className="px-6 py-4 border-t border-gray-100 bg-slate-50 flex justify-end">
                            <button
                                onClick={() => setSelectedVal(null)}
                                className="px-5 py-2 text-xs font-semibold text-white bg-[#00aea7] hover:bg-[#009b95] rounded-xl shadow-sm transition-all cursor-pointer"
                            >
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Módulo 5 — Auditoría / Auditoría y Trazabilidad
function AuditoriaPage() {
    const [selectedAudit, setSelectedAudit] = useState<any | null>(null);
    const [searchTerm, setSearchTerm] = useState("");

    const auditRecords = [
        {
            id: "13458",
            nombre: "Machine Learning for Biodiversity in Andean Ecosystems",
            metadatoRecuperado: "Abstract, Áreas ODS, Palabras clave",
            fecha: "28 jun 2024 · 09:17",
            eventos: [
                { time: "09:14:02", event: "Detección de registro", user: "Sistema CRIS", role: "Sistema", source: "DSpace local", result: "ID Registro #13458 identificado sin Abstract, Áreas ODS ni Palabras clave.", color: "#6b7a90" },
                { time: "09:14:18", event: "Recuperación de Abstract", user: "Agente IA", role: "Motor IA", source: "OpenAlex API", result: "Abstract científico recuperado e indexado desde OpenAlex (confianza 96%).", color: "#00aea7" },
                { time: "09:14:50", event: "Extracción de Palabras clave", user: "Agente IA", role: "Motor IA", source: "Extracción PDF", result: "6 palabras clave normalizadas extraídas mediante análisis OCR en texto completo.", color: "#1565C0" },
                { time: "09:15:30", event: "Clasificación en Áreas ODS", user: "Agente IA", role: "Motor IA", source: "Inferencia local", result: "ODS 15 (Vida de ecosistemas terrestres) asignado algorítmicamente.", color: "#7B1FA2" },
                { time: "09:16:15", event: "Validación humana de metadatos", user: "Carlos Fuentes", role: "Curador", source: "Módulo de Validación", result: "Abstract, Áreas ODS y Palabras clave validados técnicamente por el curador responsable.", color: "#00aea7" },
                { time: "09:16:48", event: "Aprobación humana de metadatos", user: "María González", role: "Administrador", source: "Módulo de Aprobación", result: "Metadatos aprobados en curaduría definitiva para su publicación formal en el repositorio.", color: "#F57C00" },
                { time: "09:17:03", event: "Sincronización de catálogo", user: "Agente IA", role: "Motor IA", source: "Base de datos", result: "Metadatos incorporados exitosamente en el registro #13458 de la base de datos local.", color: "#2E7D32" },
            ]
        },
        {
            id: "18954",
            nombre: "Open Science Infrastructure and Policy Frameworks in Chile",
            metadatoRecuperado: "Derechos de acceso, Palabras clave",
            fecha: "28 jun 2024 · 10:45",
            eventos: [
                { time: "10:40:12", event: "Detección de registro", user: "Sistema CRIS", role: "Sistema", source: "DSpace local", result: "Registro #18954 identificado con licencia de acceso y palabras clave faltantes.", color: "#6b7a90" },
                { time: "10:41:05", event: "Recuperación de Derechos de acceso", user: "Agente IA", role: "Motor IA", source: "Crossref API", result: "Licencia de acceso abierto Creative Commons CC BY 4.0 detectada y vinculada.", color: "#00aea7" },
                { time: "10:42:18", event: "Extracción de Palabras clave", user: "Agente IA", role: "Motor IA", source: "Extracción PDF", result: "5 palabras clave extraídas desde el pie de página y encabezado del documento PDF.", color: "#1565C0" },
                { time: "10:43:30", event: "Validación humana de metadatos", user: "Patricia Soto", role: "Validador", source: "Módulo de Validación", result: "Licencia CC BY 4.0 y lista de palabras clave verificadas contra el documento original.", color: "#00aea7" },
                { time: "10:44:20", event: "Aprobación humana de metadatos", user: "Roberto Muñoz", role: "Administrador", source: "Módulo de Aprobación", result: "Aprobación curatorial final emitida para difusión pública del registro.", color: "#F57C00" },
                { time: "10:45:00", event: "Sincronización de catálogo", user: "Agente IA", role: "Motor IA", source: "Base de datos", result: "Metadatos incorporados exitosamente en el registro #18954 de la base de datos local.", color: "#2E7D32" },
            ]
        },
        {
            id: "22103",
            nombre: "Genomic Sequencing Methods for Marine Microorganisms",
            metadatoRecuperado: "Área OCDE, Abstract",
            fecha: "27 jun 2024 · 16:20",
            eventos: [
                { time: "16:15:00", event: "Detección de registro", user: "Sistema CRIS", role: "Sistema", source: "DSpace local", result: "Registro #22103 detectado sin clasificación de Área OCDE ni resumen científico.", color: "#6b7a90" },
                { time: "16:16:30", event: "Recuperación de Área OCDE", user: "Agente IA", role: "Motor IA", source: "WoS API", result: "Clasificación 1.06 (Biología y Ciencias Biológicas) identificada en Web of Science.", color: "#00aea7" },
                { time: "16:17:45", event: "Recuperación de Abstract", user: "Agente IA", role: "Motor IA", source: "Inferencia local", result: "Abstract científico inferido y estructurado a partir del cuerpo completo del artículo.", color: "#7B1FA2" },
                { time: "16:18:30", event: "Validación humana de metadatos", user: "Mónica Araya", role: "Curador", source: "Módulo de Validación", result: "Taxonomía OCDE 1.06 y coherencia del Abstract validadas satisfactoriamente.", color: "#00aea7" },
                { time: "16:19:15", event: "Aprobación humana de metadatos", user: "Patricia Soto", role: "Administrador", source: "Módulo de Aprobación", result: "Metadatos autorizados por el curador responsable para indexación oficial.", color: "#F57C00" },
                { time: "16:20:10", event: "Sincronización de catálogo", user: "Agente IA", role: "Motor IA", source: "Base de datos", result: "Metadatos incorporados exitosamente en el registro #22103 de la base de datos local.", color: "#2E7D32" },
            ]
        },
        {
            id: "31204",
            nombre: "Nanotechnology Applications in Photovoltaic Solar Cells",
            metadatoRecuperado: "Abstract, Palabras clave, Área OCDE",
            fecha: "27 jun 2024 · 14:10",
            eventos: [
                { time: "14:02:10", event: "Detección de registro", user: "Sistema CRIS", role: "Sistema", source: "DSpace local", result: "Registro #31204 importado con vacíos en Abstract, Palabras clave y Área OCDE.", color: "#6b7a90" },
                { time: "14:03:50", event: "Recuperación de Abstract", user: "Agente IA", role: "Motor IA", source: "Scopus API", result: "Abstract científico de 280 palabras enriquecido desde Scopus (confianza 94%).", color: "#00aea7" },
                { time: "14:05:15", event: "Extracción de Palabras clave", user: "Agente IA", role: "Motor IA", source: "Inferencia local", result: "8 palabras clave especializadas en fotovoltaica extraídas semánticamente.", color: "#7B1FA2" },
                { time: "14:06:40", event: "Asignación de Área OCDE", user: "Agente IA", role: "Motor IA", source: "OpenAlex API", result: "Área OCDE 2.05 (Ingeniería de Materiales y Nanotecnología) vinculada.", color: "#00aea7" },
                { time: "14:07:50", event: "Validación humana de metadatos", user: "Fabián Escobedo", role: "Curador", source: "Módulo de Validación", result: "Revisión técnica de vocabularios controlados y taxonomía OCDE aprobada con éxito.", color: "#00aea7" },
                { time: "14:09:00", event: "Aprobación humana de metadatos", user: "María González", role: "Administrador", source: "Módulo de Aprobación", result: "Aprobación curatorial final otorgada sin requerir ediciones en el texto.", color: "#F57C00" },
                { time: "14:10:05", event: "Sincronización de catálogo", user: "Agente IA", role: "Motor IA", source: "Base de datos", result: "Metadatos incorporados exitosamente en el registro #31204 de la base de datos local.", color: "#2E7D32" },
            ]
        },
        {
            id: "14729",
            nombre: "Urban Mobility Patterns in Santiago Metropolitan Area",
            metadatoRecuperado: "Palabras clave, Áreas ODS",
            fecha: "26 jun 2024 · 11:30",
            eventos: [
                { time: "11:20:00", event: "Detección de registro", user: "Sistema CRIS", role: "Sistema", source: "DSpace local", result: "Registro #14729 identificado sin palabras clave normalizadas ni Áreas ODS.", color: "#6b7a90" },
                { time: "11:22:15", event: "Extracción de Palabras clave", user: "Agente IA", role: "Motor IA", source: "Extracción PDF", result: "6 palabras clave sobre urbanismo y movilidad normalizadas mediante OCR.", color: "#1565C0" },
                { time: "11:25:40", event: "Clasificación en Áreas ODS", user: "Agente IA", role: "Motor IA", source: "OpenAlex API", result: "ODS 11 (Ciudades y comunidades sostenibles) recuperado e indexado.", color: "#00aea7" },
                { time: "11:27:10", event: "Validación humana de metadatos", user: "Carlos Fuentes", role: "Curador", source: "Módulo de Validación", result: "Lista de palabras clave y alineación con ODS 11 validadas por experto temático.", color: "#00aea7" },
                { time: "11:28:50", event: "Aprobación humana de metadatos", user: "Roberto Muñoz", role: "Administrador", source: "Módulo de Aprobación", result: "Metadatos autorizados formalmente en el panel de aprobación curatorial.", color: "#F57C00" },
                { time: "11:30:12", event: "Sincronización de catálogo", user: "Agente IA", role: "Motor IA", source: "Base de datos", result: "Metadatos incorporados exitosamente en el registro #14729 de la base de datos local.", color: "#2E7D32" },
            ]
        }
    ];

    const filtered = auditRecords.filter(r =>
        r.id.includes(searchTerm) ||
        r.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.metadatoRecuperado.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="h-full overflow-y-auto">
            <SectionHeader title="Auditoría y Trazabilidad" description="Listado de registros del catálogo científico y su historial completo de eventos de enriquecimiento y curaduría." />

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <Card className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-semibold text-[#6b7a90] uppercase">Registros Auditados</span>
                        <div className="w-8 h-8 rounded-lg bg-teal-50 text-[#00aea7] flex items-center justify-center"><ClipboardList size={16} /></div>
                    </div>
                    <p className="text-xl font-bold text-[#1a2332]">{auditRecords.length} <span className="text-xs font-normal text-[#6b7a90]">registros</span></p>
                    <p className="text-[10px] text-[#00aea7] font-medium mt-0.5">Trazabilidad en log</p>
                </Card>
                <Card className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-semibold text-[#6b7a90] uppercase">Eventos Registrados</span>
                        <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center"><Activity size={16} /></div>
                    </div>
                    <p className="text-xl font-bold text-[#1a2332]">20 <span className="text-xs font-normal text-[#6b7a90]">eventos</span></p>
                    <p className="text-[10px] text-blue-600 font-medium mt-0.5">Promedio 4 eventos por registro</p>
                </Card>
                <Card className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-semibold text-[#6b7a90] uppercase">Fuentes Consultadas</span>
                        <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center"><Database size={16} /></div>
                    </div>
                    <p className="text-xl font-bold text-[#1a2332]">4 <span className="text-xs font-normal text-[#6b7a90]">fuentes</span></p>
                    <p className="text-[10px] text-purple-600 font-medium mt-0.5">Scopus, WoS, Crossref, OpenAlex</p>
                </Card>
                <Card className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-semibold text-[#6b7a90] uppercase">Integridad de metadatos</span>
                        <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center"><ShieldCheck size={16} /></div>
                    </div>
                    <p className="text-xl font-bold text-emerald-700">100%</p>
                    <p className="text-[10px] text-emerald-600 font-medium mt-0.5">Sin alertas de inconsistencia</p>
                </Card>
            </div>

            <Card>
                <div className="p-4 border-b border-gray-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="relative flex-1 max-w-xs">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7a90]" />
                        <input
                            type="text"
                            placeholder="Buscar por ID, nombre o metadato..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-50 bg-slate-50/50">
                                {["ID del registro", "Nombre del registro asociado", "Metadatos recuperados", "Última actualización", "Acciones"].map((h) => (
                                    <th key={h} className="text-left px-4 py-3.5 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide whitespace-nowrap">
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((row) => (
                                <tr key={row.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <span className="text-xs font-mono font-bold text-[#1565C0] bg-blue-50/80 border border-blue-100 px-2.5 py-1 rounded-md">#{row.id}</span>
                                    </td>
                                    <td className="px-4 py-3.5 max-w-[280px]">
                                        <p className="text-xs font-semibold text-[#1a2332] truncate" title={row.nombre}>{row.nombre}</p>
                                    </td>
                                    <td className="px-4 py-3.5">
                                        <div className="flex flex-wrap gap-1">
                                            {row.metadatoRecuperado.split(", ").map((meta: string) => (
                                                <span key={meta} className="text-[11px] font-medium px-2 py-0.5 bg-teal-50 text-[#00aea7] rounded border border-teal-100 whitespace-nowrap">
                                                    {meta}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <span className="text-xs text-slate-500 font-mono">{row.fecha}</span>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <button
                                            onClick={() => setSelectedAudit(row)}
                                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-[#00aea7] hover:opacity-90 transition-all rounded-lg shadow-2xs cursor-pointer"
                                            title="Visualizar la auditoría y trazabilidad del registro asociado"
                                        >
                                            <ClipboardList size={13} /> Ver auditoría
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {filtered.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-4 py-8 text-center text-xs text-slate-400">
                                        No se encontraron registros en la auditoría que coincidan con la búsqueda.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </Card>

            {/* Modal Trazabilidad y Auditoría */}
            {selectedAudit && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in duration-150">
                    <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 w-full max-w-2xl max-h-[85vh] overflow-hidden animate-in zoom-in-95 duration-150 flex flex-col">
                        <div className="px-6 py-4 border-b border-gray-100 bg-slate-50 flex items-center justify-between">
                            <div className="flex items-center gap-2.5">
                                <div className="w-8 h-8 rounded-lg bg-[#00aea7]/10 text-[#00aea7] flex items-center justify-center font-bold">
                                    <ClipboardList size={18} />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-slate-800">Trazabilidad y Auditoría — Registro #{selectedAudit.id}</h3>
                                    <p className="text-[11px] text-slate-500">Historial completo de enriquecimiento algorítmico y curaduría</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => alert(`Exportando reporte de auditoría completo para el registro #${selectedAudit.id}...`)}
                                    className="flex items-center gap-1.5 px-3 py-1 text-xs font-medium text-slate-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer shadow-2xs"
                                >
                                    <Download size={13} /> Exportar log
                                </button>
                                <button
                                    onClick={() => setSelectedAudit(null)}
                                    className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors cursor-pointer"
                                >
                                    <X size={18} />
                                </button>
                            </div>
                        </div>

                        <div className="p-6 overflow-y-auto space-y-5 flex-1">
                            <div className="bg-slate-50 p-4 rounded-xl border border-gray-100 space-y-2">
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Nombre del Registro Asociado</span>
                                        <p className="text-xs font-bold text-slate-800 mt-0.5">{selectedAudit.nombre}</p>
                                    </div>
                                    <div className="text-right shrink-0">
                                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Identificador</span>
                                        <span className="text-xs font-mono font-bold text-[#1565C0]">#{selectedAudit.id}</span>
                                    </div>
                                </div>
                                <div className="pt-2 border-t border-gray-200/60 flex items-center justify-between">
                                    <span className="text-[11px] font-medium text-slate-500">Metadatos recuperados y enriquecidos:</span>
                                    <span className="text-xs font-semibold text-[#00aea7]">{selectedAudit.metadatoRecuperado}</span>
                                </div>
                            </div>

                            <div>
                                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-4 flex items-center gap-1.5">
                                    <Activity size={14} className="text-[#00aea7]" /> Cronología de Enriquecimiento y Curaduría
                                </h4>
                                <div className="relative pl-2">
                                    {selectedAudit.eventos.map((ev: any, i: number) => (
                                        <div key={i} className="flex gap-4 mb-0">
                                            <div className="flex flex-col items-center">
                                                <div className="w-8 h-8 rounded-full border-2 flex items-center justify-center flex-shrink-0 bg-white" style={{ borderColor: ev.color }}>
                                                    <div className="w-2.5 h-2.5 rounded-full" style={{ background: ev.color }} />
                                                </div>
                                                {i < selectedAudit.eventos.length - 1 && <div className="w-0.5 flex-1 min-h-[32px]" style={{ background: `${ev.color}30` }} />}
                                            </div>
                                            <div className="pb-6 flex-1 min-w-0">
                                                <div className="flex items-start justify-between gap-2 bg-white p-3 rounded-xl border border-gray-100 shadow-2xs">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <p className="text-xs font-bold text-[#1a2332]">{ev.event}</p>
                                                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium border border-slate-200/60">{ev.source}</span>
                                                        </div>
                                                        <p className="text-xs text-slate-600 mt-1 font-medium">{ev.result}</p>
                                                    </div>
                                                    <div className="text-right flex-shrink-0">
                                                        <p className="text-[11px] font-mono font-semibold text-slate-500">{ev.time}</p>
                                                        <p className="text-[11px] font-bold text-[#1a2332] mt-0.5">{ev.user}</p>
                                                        {ev.role && (
                                                            <span className={`inline-block text-[10px] font-semibold px-2 py-0.5 rounded-md mt-1 ${ev.role === "Administrador" ? "bg-amber-100 text-amber-800 border border-amber-300" :
                                                                ev.role === "Validador" || ev.role === "Curador" ? "bg-purple-100 text-purple-800 border border-purple-300" :
                                                                    "bg-teal-50 text-[#00aea7] border border-teal-200"
                                                                }`}>
                                                                {ev.role}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="px-6 py-4 border-t border-gray-100 bg-slate-50/60 flex items-center justify-end">
                            <button
                                onClick={() => setSelectedAudit(null)}
                                className="px-5 py-1.5 rounded-lg text-xs font-semibold text-white bg-[#00aea7] hover:opacity-90 transition-opacity cursor-pointer shadow-xs"
                            >
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Módulo 6 — Aprobación de metadatos
function AprobacionPage() {
    const [decisions, setDecisions] = useState<Record<number, string>>({});
    const [comparingRow, setComparingRow] = useState<any | null>(null);
    const [filterHistory, setFilterHistory] = useState("Todos");

    const initialHistory = [
        { registro: "#09871", campo: "Área ODS", valor: "ODS 13: Acción por el clima", fuente: "Scopus", responsable: "Patricia Soto", rol: "Curador", estado: "aprobado", fecha: "Hoy, 11:30" },
        { registro: "#14729", campo: "Derechos de acceso", valor: "Acceso Abierto (Creative Commons CC BY-NC 4.0)", fuente: "Crossref", responsable: "Mónica Araya", rol: "Administrador", estado: "editado", fecha: "Hoy, 10:15" },
        { registro: "#28331", campo: "Área OCDE", valor: "102 Informática y Ciencias de la Información (1.02)", fuente: "WoS", responsable: "Fabián Escobedo", rol: "Curador", estado: "aprobado", fecha: "Ayer, 17:40" },
        { registro: "#19042", campo: "Palabras clave", valor: "redes neuronales, aprendizaje profundo, visión por computador", fuente: "OpenAlex", responsable: "Carlos Fuentes", rol: "Administrador", estado: "rechazado", fecha: "Ayer, 15:20" },
        { registro: "#33109", campo: "Abstract", valor: "Estudio comparativo sobre algoritmos de optimización en redes eléctricas...", fuente: "Extracción directa de PDF", responsable: "María González", rol: "Curador", estado: "aprobado", fecha: "28 jun, 14:10" },
        { registro: "#11204", campo: "Área ODS", valor: "ODS 4: Educación de calidad", fuente: "Scopus", responsable: "Roberto Muñoz", rol: "Administrador", estado: "rechazado", fecha: "28 jun, 11:05" },
    ];

    const decidedFromPending = aprobacionData
        .map((row, idx) => ({
            ...row,
            estado: decisions[idx],
            fecha: "Justo ahora",
        }))
        .filter((row) => row.estado);

    const allResolved = [...decidedFromPending, ...initialHistory];
    const filteredHistory = allResolved.filter((row) => {
        if (filterHistory === "Todos") return true;
        if (filterHistory === "Aprobados") return row.estado === "aprobado";
        if (filterHistory === "Editados") return row.estado === "editado";
        if (filterHistory === "Rechazados") return row.estado === "rechazado";
        return true;
    });

    return (
        <div className="h-full overflow-y-auto">
            <SectionHeader title="Aprobación de metadatos" description="Revisión y aprobación de sugerencias de metadatos previamente validados." />

            <div className="flex gap-4 mb-5">
                {[
                    { label: "Pendientes", value: "123", color: "#F57C00", bg: "#fff3e0" },
                    { label: "Aprobados", value: "47", color: "#2E7D32", bg: "#e8f5e9" },
                    { label: "Rechazados", value: "8", color: "#d32f2f", bg: "#ffebee" },
                    { label: "Editados", value: "12", color: "#1565C0", bg: "#e3f2fd" },
                ].map((s) => (
                    <Card key={s.label} className="flex-1 px-4 py-3">
                        <p className="text-[11px] text-[#6b7a90] mb-1">{s.label}</p>
                        <p className="text-xl font-semibold" style={{ color: s.color }}>{s.value}</p>
                    </Card>
                ))}
            </div>

            <Card>
                <div className="p-4 border-b border-gray-50 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-[#1a2332]">Sugerencias pendientes de aprobación</h3>
                    <div className="flex gap-2">
                        <button
                            onClick={() => alert("Los registros rechazados han sido reiniciados para re-procesarse automáticamente con el agente inteligente.")}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-teal-200 rounded-lg text-[#007a75] bg-teal-50/50 hover:bg-teal-50 cursor-pointer font-medium"
                        >
                            <RefreshCw size={12} /> Re-procesar rechazados
                        </button>
                        <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-200 rounded-lg text-[#6b7a90] hover:bg-gray-50">
                            <Filter size={12} /> Filtrar
                        </button>
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-50">
                                {["Registro", "Metadato", "Valor sugerido", "Fuente", "Confianza", "Responsable", "Acción"].map((h) => (
                                    <th key={h} className="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide whitespace-nowrap">
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {aprobacionData.map((row, i) => (
                                <tr key={i} className="border-b border-gray-50 hover:bg-gray-50/40 transition-colors">
                                    <td className="px-4 py-4 text-xs font-mono font-medium text-[#1565C0] whitespace-nowrap">{row.registro}</td>
                                    <td className="px-4 py-4">
                                        <span className="text-xs font-medium px-2 py-0.5 bg-blue-50 text-blue-700 rounded">{row.campo}</span>
                                    </td>
                                    <td className="px-4 py-4 text-xs text-[#1a2332] max-w-[240px]">
                                        <p className="truncate">{row.valor}</p>
                                    </td>
                                    <td className="px-4 py-4 text-xs text-[#6b7a90] whitespace-nowrap">{row.fuente}</td>
                                    <td className="px-4 py-4 whitespace-nowrap">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                <div className="h-full rounded-full" style={{ width: `${row.confianza}%`, background: row.confianza >= 90 ? "#00aea7" : "#F57C00" }} />
                                            </div>
                                            <span className="text-xs font-semibold" style={{ color: row.confianza >= 90 ? "#2E7D32" : "#F57C00" }}>{row.confianza}%</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 text-xs text-[#6b7a90] whitespace-nowrap">{row.responsable}</td>
                                    <td className="px-4 py-4">
                                        {decisions[i] ? (
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs font-medium px-2 py-1 rounded-lg" style={{
                                                    background: decisions[i] === "aprobado" ? "#e8f5e9" : decisions[i] === "rechazado" ? "#ffebee" : "#e3f2fd",
                                                    color: decisions[i] === "aprobado" ? "#2E7D32" : decisions[i] === "rechazado" ? "#d32f2f" : "#1565C0",
                                                }}>
                                                    {decisions[i] === "aprobado" ? "Aprobado" : decisions[i] === "rechazado" ? "Rechazado" : "Editado"}
                                                </span>
                                                {decisions[i] === "rechazado" && (
                                                    <button
                                                        onClick={() => {
                                                            alert("Iniciando nuevo ciclo de enriquecimiento para el registro #" + row.registro);
                                                            setDecisions(d => ({ ...d, [i]: "" }));
                                                        }}
                                                        title="Procesar nuevamente este registro"
                                                        className="px-2 py-0.5 text-[10px] font-bold text-white bg-[#00aea7] rounded hover:opacity-90 transition-opacity cursor-pointer"
                                                    >
                                                        Re-procesar
                                                    </button>
                                                )}
                                            </div>
                                        ) : (
                                            <div className="flex gap-1.5 items-center">
                                                <button
                                                    onClick={() => setComparingRow(row)}
                                                    className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-lg transition-colors cursor-pointer mr-0.5"
                                                    title="Comparar metadato actual en DSpace vs. propuesta IA"
                                                >
                                                    <Bot size={13} /> Comparar
                                                </button>
                                                <button onClick={() => setDecisions(d => ({ ...d, [i]: "aprobado" }))} className="px-2.5 py-1 text-[11px] font-medium text-white rounded-lg hover:opacity-90 cursor-pointer" style={{ background: "#00aea7" }}>
                                                    Aprobar
                                                </button>
                                                <button onClick={() => setDecisions(d => ({ ...d, [i]: "editado" }))} className="px-2.5 py-1 text-[11px] font-medium text-[#F57C00] border border-[#F57C00]/30 rounded-lg hover:bg-[#F57C00]/5 cursor-pointer">
                                                    Editar
                                                </button>
                                                <button onClick={() => setDecisions(d => ({ ...d, [i]: "rechazado" }))} className="px-2.5 py-1 text-[11px] font-medium text-[#d32f2f] border border-red-200 rounded-lg hover:bg-red-50 cursor-pointer">
                                                    Rechazar
                                                </button>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </Card>

            {/* Tabla de Metadatos Procesados (Aprobados, Editados y Rechazados) */}
            <Card className="mt-6">
                <div className="p-4 border-b border-gray-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                        <h3 className="text-sm font-semibold text-[#1a2332]">Historial de resoluciones (Metadatos Aprobados, Editados y Rechazados)</h3>
                        <p className="text-[11px] text-[#6b7a90] mt-0.5">Registro histórico y en tiempo real de las decisiones curatoriales sobre metadatos.</p>
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {["Todos", "Aprobados", "Editados", "Rechazados"].map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilterHistory(f)}
                                className="px-3 py-1.5 text-xs rounded-lg font-medium transition-all cursor-pointer border border-gray-200/60"
                                style={{
                                    background: filterHistory === f ? "#00aea7" : "#f8fafc",
                                    color: filterHistory === f ? "#fff" : "#6b7a90",
                                    borderColor: filterHistory === f ? "#00aea7" : "#e2e8f0",
                                }}
                            >
                                {f}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-50 bg-slate-50/60">
                                {["Registro", "Campo", "Valor resuelto", "Fuente", "Responsable", "Rol", "Resolución", "Fecha / Hora"].map((h) => (
                                    <th key={h} className="text-left px-4 py-3.5 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide whitespace-nowrap">
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filteredHistory.map((row, idx) => (
                                <tr key={idx} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                                    <td className="px-4 py-3.5 text-xs font-mono font-medium text-[#1565C0] whitespace-nowrap">{row.registro}</td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <span className="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md border border-blue-100">{row.campo}</span>
                                    </td>
                                    <td className="px-4 py-3.5 text-xs text-[#1a2332] max-w-[280px]">
                                        <p className="truncate font-medium">{row.valor}</p>
                                    </td>
                                    <td className="px-4 py-3.5 text-xs text-slate-600 whitespace-nowrap">
                                        <span className="font-semibold">{row.fuente}</span>
                                    </td>
                                    <td className="px-4 py-3.5 text-xs text-slate-600 whitespace-nowrap">{row.responsable}</td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-md border ${row.rol === 'Administrador' ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-purple-50 text-purple-700 border-purple-200'}`}>
                                            {row.rol || "Curador"}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3.5 whitespace-nowrap">
                                        <span
                                            className="text-xs font-bold px-2.5 py-1 rounded-lg inline-flex items-center gap-1 shadow-2xs"
                                            style={{
                                                background: row.estado === "aprobado" ? "#e8f5e9" : row.estado === "rechazado" ? "#ffebee" : "#e3f2fd",
                                                color: row.estado === "aprobado" ? "#2E7D32" : row.estado === "rechazado" ? "#d32f2f" : "#1565C0",
                                                border: `1px solid ${row.estado === "aprobado" ? "#c8e6c9" : row.estado === "rechazado" ? "#ffcdd2" : "#bbdefb"}`,
                                            }}
                                        >
                                            {row.estado === "aprobado" ? "Aprobado" : row.estado === "rechazado" ? "Rechazado" : "Editado"}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3.5 text-xs text-slate-400 whitespace-nowrap font-mono">{row.fecha}</td>
                                </tr>
                            ))}
                            {filteredHistory.length === 0 && (
                                <tr>
                                    <td colSpan={8} className="px-4 py-8 text-center text-xs text-slate-400">
                                        No hay metadatos registrados en esta categoría.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </Card>

            {/* Modal de Curación y Comparación Humana (Metadato Actual vs Propuesta IA) */}
            {comparingRow && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in duration-150">
                    <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-150 flex flex-col">
                        <div className="px-6 py-4 border-b border-gray-100 bg-slate-50 flex items-center justify-between">
                            <div className="flex items-center gap-2.5">
                                <div className="w-8 h-8 rounded-lg bg-blue-600/10 text-blue-600 flex items-center justify-center font-bold">
                                    <CheckSquare size={18} />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-slate-800">Decisión Curatorial: Comparación y Aprobación</h3>
                                    <p className="text-[11px] text-slate-500">Registro #{comparingRow.registro} — Campo: {comparingRow.campo}</p>
                                </div>
                            </div>
                            <button onClick={() => setComparingRow(null)} className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors cursor-pointer">
                                <X size={18} />
                            </button>
                        </div>

                        <div className="p-6 space-y-5">


                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="bg-gray-50 rounded-xl p-4 border border-gray-200 space-y-2">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Metadato Actual en DSpace</span>
                                    <p className="text-xs text-slate-600 leading-relaxed font-mono bg-white p-2.5 rounded border border-gray-200/60">
                                        {comparingRow.campo === "DOI" ? "(vacío / no asignado)" : comparingRow.campo === "Licencia" ? "Derechos reservados genéricos" : "(sin indexar en vocabulario controlado)"}
                                    </p>
                                    <span className="text-[11px] text-slate-400 block italic">Estado: Incompleto / Faltante</span>
                                </div>

                                <div className="bg-emerald-50/60 rounded-xl p-4 border border-emerald-200/80 space-y-2">
                                    <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider block">Propuesta Validada</span>
                                    <p className="text-xs text-emerald-950 font-medium leading-relaxed bg-white p-2.5 rounded border border-emerald-200 shadow-2xs">
                                        {comparingRow.valor}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="px-6 py-4 border-t border-gray-100 bg-slate-50 flex items-center justify-between gap-3">
                            <span className="text-xs text-slate-500">Responsable validador: {comparingRow.responsable}</span>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setComparingRow(null)}
                                    className="px-3.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200/60 rounded-xl transition-colors cursor-pointer"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={() => {
                                        alert(`El metadato para el registro #${comparingRow.registro} fue RECHAZADO por el curador y devuelto al motor de IA.`);
                                        setComparingRow(null);
                                    }}
                                    className="flex items-center gap-1 px-3.5 py-1.5 text-xs font-bold text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl transition-colors cursor-pointer"
                                >
                                    <X size={14} /> Rechazar
                                </button>
                                <button
                                    onClick={() => {
                                        alert(`El metadato para el registro #${comparingRow.registro} fue APROBADO por el curador y está listo para sincronización con DSpace-CRIS.`);
                                        setComparingRow(null);
                                    }}
                                    className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold text-white bg-[#00aea7] hover:bg-[#009b95] rounded-xl shadow-sm transition-all cursor-pointer"
                                >
                                    <CheckSquare size={14} /> Aprobar y Sincronizar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Reportes y Estadísticas de Recuperación (Unificado)
function ReportesPage() {
    const weeklyData = [
        { week: "16-06-2026", enriquecidos: 820, detectados: 1100, aprobados: 740 },
        { week: "23-06-2026", enriquecidos: 943, detectados: 1240, aprobados: 880 },
        { week: "30-06-2026", enriquecidos: 1102, detectados: 1380, aprobados: 1020 },
        { week: "07-07-2026", enriquecidos: 987, detectados: 1290, aprobados: 910 },
    ];

    return (
        <div className="h-full overflow-y-auto space-y-6">
            <SectionHeader title="Reportes y Estadísticas de Recuperación" description="Análisis integral del rendimiento del agente inteligente, consultas y conectividad con fuentes externas." />

            {/* Selector de período y exportación */}
            <div className="flex items-center gap-3">
                {["Esta semana", "Este mes", "Último trimestre"].map((p, i) => (
                    <button
                        key={p}
                        className="px-4 py-2 text-xs rounded-lg font-medium transition-all"
                        style={{ background: i === 1 ? "#00aea7" : "#f0f4f8", color: i === 1 ? "#fff" : "#6b7a90" }}
                    >
                        {p}
                    </button>
                ))}
                <button
                    className="ml-auto flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white rounded-lg hover:opacity-90 shadow-2xs cursor-pointer"
                    style={{ background: "#F57C00" }}
                >
                    <Download size={13} /> Exportar PDF
                </button>
            </div>

            {/* Sección 1: Rendimiento y Actividad General */}
            <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#6b7a90] mb-3">1. Rendimiento y Actividad General del Agente IA</h3>
                <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-4">
                    {[
                        { label: "Registros procesados", value: "3.852", delta: "+12%", up: true },
                        { label: "Tasa de éxito", value: "96.4%", delta: "+2.1%", up: true },
                        { label: "Validaciones realizadas", value: "20", up: true },
                        { label: "Aprobaciones realizadas", value: "18", up: false },
                    ].map((s) => (
                        <Card key={s.label} className="p-4">
                            <p className="text-xs text-[#6b7a90] mb-1">{s.label}</p>
                            <p className="text-xl font-semibold text-[#1a2332]">{s.value}</p>
                        </Card>
                    ))}
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                    <Card className="p-5 xl:col-span-2">
                        <h3 className="text-sm font-semibold text-[#1a2332] mb-4">Actividad mensual por semana</h3>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={weeklyData} barSize={20} barGap={4}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f0f4f8" vertical={false} />
                                <XAxis dataKey="week" tick={{ fontSize: 12, fill: "#6b7a90" }} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fontSize: 12, fill: "#6b7a90" }} axisLine={false} tickLine={false} />
                                <Tooltip contentStyle={{ border: "1px solid #e8eef4", borderRadius: 8, fontSize: 12 }} />
                                <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
                                <Bar dataKey="detectados" name="Detectados" fill="#1f92ff" radius={[4, 4, 0, 0]} />
                                <Bar dataKey="enriquecidos" name="Enriquecidos" fill="#00aea7" radius={[4, 4, 0, 0]} />
                                <Bar dataKey="aprobados" name="Aprobados" fill="#F57C00" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </Card>

                    <Card className="p-5 xl:col-span-1 flex flex-col justify-between">
                        <h3 className="text-sm font-semibold text-[#1a2332] mb-4">Distribución por tipo de campo</h3>
                        <div className="flex flex-col items-center gap-4 my-auto">
                            <ResponsiveContainer width={150} height={150}>
                                <PieChart>
                                    <Pie data={donutData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" strokeWidth={0}>
                                        {donutData.map((entry, i) => (
                                            <Cell key={i} fill={entry.color} />
                                        ))}
                                    </Pie>
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="w-full space-y-2 pt-2 border-t border-gray-50">
                                {donutData.map((d) => (
                                    <div key={d.name} className="flex items-center gap-2">
                                        <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: d.color }} />
                                        <span className="text-xs text-[#6b7a90] truncate">{d.name}</span>
                                        <span className="text-xs font-semibold text-[#1a2332] ml-auto pl-2">{d.value}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </Card>
                </div>
            </div>

            {/* Sección 2: Estadísticas de Recuperación desde Fuentes Externas (Migrado desde RecuperacionPage) */}
            <div className="pt-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#6b7a90] mb-3">2. Estadísticas de Recuperación y Conectividad con Fuentes Externas</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    {apiSources.map((api) => (
                        <Card key={api.name} className="p-5">
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-[#e0f7f6] flex items-center justify-center">
                                        <Globe size={18} style={{ color: "#00aea7" }} />
                                    </div>
                                    <div>
                                        <h3 className="text-sm font-semibold text-[#1a2332]">{api.name}</h3>
                                        <p className="text-[11px] text-[#6b7a90]">Última consulta: {api.lastQuery}</p>
                                    </div>
                                </div>
                                <Badge color={api.status}>{api.status}</Badge>
                            </div>

                            <div className="grid grid-cols-3 gap-3">
                                <div className="bg-gray-50 rounded-lg p-3 text-center">
                                    <p className="text-xs text-[#6b7a90] mb-1">Metadatos recuperados</p>
                                    <p className="text-sm font-semibold text-[#1a2332]">{api.recovered.toLocaleString()}</p>
                                </div>
                                <div className="bg-gray-50 rounded-lg p-3 text-center">
                                    <p className="text-xs text-[#6b7a90] mb-1">Consultas realizadas</p>
                                    <p className="text-sm font-semibold text-[#1a2332]">{api.queries.toLocaleString()}</p>
                                </div>
                                <div className="bg-gray-50 rounded-lg p-3 text-center">
                                    <p className="text-xs text-[#6b7a90] mb-1">Disponibilidad</p>
                                    <p className="text-sm font-semibold" style={{ color: api.availability > 99 ? "#2E7D32" : "#F57C00" }}>
                                        {api.availability}%
                                    </p>
                                </div>
                            </div>

                            <div className="mt-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                <div className="h-full rounded-full transition-all" style={{ width: `${api.availability}%`, background: api.availability > 99 ? "#00aea7" : "#F57C00" }} />
                            </div>

                            <div className="mt-3 flex items-center gap-2">
                                <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-[#00aea7] border border-[#00aea7]/30 rounded-lg hover:bg-[#00aea7]/5 transition-colors cursor-pointer">
                                    <RefreshCw size={12} /> Actualizar
                                </button>
                                <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-[#6b7a90] border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                                    <ExternalLink size={12} /> Documentación
                                </button>
                            </div>
                        </Card>
                    ))}
                </div>

                <Card className="p-5">
                    <h3 className="text-sm font-semibold text-[#1a2332] mb-4">Consultas vs Metadatos recuperados por fuente externa</h3>
                    <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={apiSources.map((a) => ({ name: a.name.split(" ")[0], consultas: a.queries, recuperados: a.recovered }))} barSize={24}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f4f8" vertical={false} />
                            <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#6b7a90" }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fontSize: 12, fill: "#6b7a90" }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{ border: "1px solid #e8eef4", borderRadius: 8, fontSize: 12 }} />
                            <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
                            <Bar dataKey="consultas" fill="#99e8e6" radius={[4, 4, 0, 0]} name="Consultas realizadas" />
                            <Bar dataKey="recuperados" fill="#00aea7" radius={[4, 4, 0, 0]} name="Metadatos recuperados" />
                        </BarChart>
                    </ResponsiveContainer>
                </Card>
            </div>
        </div>
    );
}

// Configuración
function ConfiguracionPage() {
    const llmModel = "Qwen3 32B";
    const [threshold, setThreshold] = useState(85);
    const [autoApprove, setAutoApprove] = useState(false);

    return (
        <div className="h-full overflow-y-auto">
            <SectionHeader title="Configuración del Sistema" description="Parámetros del agente IA, modelos de lenguaje y conexiones externas." />

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <Card className="p-5">
                    <h3 className="text-sm font-semibold text-[#1a2332] mb-4">Modelo de IA</h3>
                    <div className="flex flex-col gap-3">
                        <div>
                            <label className="text-xs text-[#6b7a90] mb-1 block">Modelo LLM activo</label>
                            <div className="flex items-center justify-between px-3 py-2.5 border border-gray-200 rounded-lg bg-gray-50 text-[#1a2332] text-xs">
                                <div className="flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-[#00aea7]" />
                                    <span className="font-semibold text-[#1a2332]">{llmModel}</span>
                                </div>
                                <span className="text-[10px] font-medium text-[#007a75] bg-[#e0f7f6] px-2.5 py-0.5 rounded-full border border-[#99e8e6]">
                                    Modelo único
                                </span>
                            </div>
                        </div>
                    </div>
                </Card>

                <Card className="p-5">
                    <h3 className="text-sm font-semibold text-[#1a2332] mb-4">Conexiones DSpace-CRIS</h3>
                    <div className="flex flex-col gap-3">
                        {[
                            { label: "URL base DSpace", value: "https://repositorio.usach.cl/api" },
                            { label: "Token API", value: "••••••••••••••••••••••••" },
                            { label: "Intervalo de sincronización", value: "Cada 6 horas" },
                            { label: "Modo de integración y seguridad", value: "Staging / Pre-incorporación (Sin modificar BD productiva)" },
                        ].map((f) => (
                            <div key={f.label}>
                                <label className="text-xs text-[#6b7a90] mb-1 block">{f.label}</label>
                                <input type="text" defaultValue={f.value} className="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 text-[#1a2332] focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]" />
                            </div>
                        ))}
                    </div>
                </Card>

                <Card className="p-5 xl:col-span-2">
                    <h3 className="text-sm font-semibold text-[#1a2332] mb-4">Fuentes de enriquecimiento habilitadas</h3>
                    <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
                        {apiSources.map((api) => (
                            <div key={api.name} className="flex items-center justify-between p-3 rounded-lg border border-gray-100 bg-gray-50">
                                <span className="text-xs font-medium text-[#1a2332]">{api.name}</span>
                                <div className="w-8 h-4 rounded-full bg-[#00aea7] relative cursor-pointer">
                                    <div className="absolute top-0.5 right-0.5 h-3 w-3 rounded-full bg-white shadow" />
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="mt-4 flex gap-2">
                        <button className="px-4 py-2 text-xs font-medium text-white rounded-lg hover:opacity-90" style={{ background: "#00aea7" }}>
                            Guardar cambios
                        </button>
                        <button className="px-4 py-2 text-xs font-medium text-[#6b7a90] border border-gray-200 rounded-lg hover:bg-gray-50">
                            Cancelar
                        </button>
                    </div>
                </Card>
            </div>
        </div>
    );
}

// Perfil
function PerfilPage() {
    return (
        <div className="h-full overflow-y-auto">
            <SectionHeader title="Perfil de Usuario" description="Información personal y configuración de acceso al sistema." />

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                <Card className="p-5 text-center">
                    <div className="w-20 h-20 rounded-2xl flex items-center justify-center text-white text-2xl font-bold mx-auto mb-3" style={{ background: "#00aea7" }}>
                        AV
                    </div>
                    <h3 className="text-base font-semibold text-[#1a2332]">Administrador VRIIC</h3>
                    <p className="text-xs text-[#6b7a90] mb-1">admin.vriic@usach.cl</p>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-[#e0f7f6] text-[#007a75] border border-[#99e8e6]">
                        Administrador
                    </span>
                    <div className="mt-4 pt-4 border-t border-gray-50 grid grid-cols-2 gap-3">
                        <div className="text-center">
                            <p className="text-lg font-semibold text-[#1a2332]">1.847</p>
                            <p className="text-[11px] text-[#6b7a90]">Aprobaciones</p>
                        </div>
                        <div className="text-center">
                            <p className="text-lg font-semibold text-[#1a2332]">94.2%</p>
                            <p className="text-[11px] text-[#6b7a90]">Tasa aceptación</p>
                        </div>
                    </div>
                </Card>

                <Card className="xl:col-span-2 p-5">
                    <h3 className="text-sm font-semibold text-[#1a2332] mb-4">Información del usuario</h3>
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                        {[
                            { label: "Nombre completo", value: "Administrador del Sistema" },
                            { label: "Correo electrónico", value: "admin.vriic@usach.cl" },
                            { label: "Unidad", value: "Vicerrectoría de Investigación, Innovación y Creación" },
                            { label: "Institución", value: "Universidad de Santiago de Chile" },
                            { label: "Último acceso", value: "28 jun 2024 — 09:02" },
                        ].map((f) => (
                            <div key={f.label}>
                                <label className="text-xs text-[#6b7a90] mb-1 block">{f.label}</label>
                                <input type="text" defaultValue={f.value} className="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 text-[#1a2332] focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]" />
                            </div>
                        ))}
                    </div>
                    <div className="flex gap-2 mt-4">
                        <button className="px-4 py-2 text-xs font-medium text-white rounded-lg hover:opacity-90" style={{ background: "#00aea7" }}>
                            Guardar cambios
                        </button>
                        <button className="px-4 py-2 text-xs font-medium border border-gray-200 text-[#6b7a90] rounded-lg hover:bg-gray-50">
                            Cambiar contraseña
                        </button>
                    </div>
                </Card>

                <Card className="xl:col-span-3 p-5">
                    <h3 className="text-sm font-semibold text-[#1a2332] mb-3">Permisos y roles</h3>
                    <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
                        {[
                            { perm: "Ver registros", granted: true },
                            { perm: "Aprobar metadatos", granted: true },
                            { perm: "Configurar sistema", granted: true },
                            { perm: "Gestionar usuarios", granted: true },
                            { perm: "Exportar reportes", granted: true },
                            { perm: "Acceso API externo", granted: true },
                            { perm: "Eliminar registros", granted: false },
                        ].map((p) => (
                            <div key={p.perm} className="flex items-center gap-2 p-2.5 rounded-lg border border-gray-100 bg-gray-50">
                                <div className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: p.granted ? "#e0f7f6" : "#ffebee" }}>
                                    <div className="w-2 h-2 rounded-full" style={{ background: p.granted ? "#00aea7" : "#d32f2f" }} />
                                </div>
                                <span className="text-[11px] text-[#1a2332]">{p.perm}</span>
                            </div>
                        ))}
                    </div>
                </Card>
            </div>
        </div>
    );
}

// ─── Módulo Gestión de Usuarios y Permisos ──────────────────────────────
const initialUsers = [
    {
        id: "USR-001",
        name: "Fabián Escobedo",
        email: "fabian.escobedo@usach.cl",
        role: "Administrador",
        status: "Activo" as const,
        permissions: ["Gestión total del sistema", "Crear/Revocar usuarios", "Configuración LLM", "Aprobación de metadatos", "Sincronización OAI-PMH"],
        department: "VRIIC · Dirección de Investigación",
        lastActive: "En línea ahora"
    },
    {
        id: "USR-002",
        name: "María González",
        email: "maria.gonzalez@usach.cl",
        role: "Curador",
        status: "Activo" as const,
        permissions: ["Aprobación de metadatos", "Validación sugerencias IA", "Ver monitoreo y alertas", "Análisis documental PDF"],
        department: "VRIIC · Curaduría",
        lastActive: "Hace 14 min"
    },
    {
        id: "USR-003",
        name: "Roberto Muñoz",
        email: "roberto.munoz@usach.cl",
        role: "Perfil académico",
        status: "Activo" as const,
        permissions: ["Sincronización OAI-PMH", "Forzar re-indexación", "Ver monitoreo y alertas", "Ver auditoría"],
        department: "VRIIC · Gestión de repositorios",
        lastActive: "Hace 2 horas"
    },
    {
        id: "USR-004",
        name: "Patricia Soto",
        email: "patricia.soto@usach.cl",
        role: "Usuario externo",
        status: "Revocado" as const,
        permissions: ["Ver auditoría", "Exportar reportes de calidad"],
        department: "Facultad de Humanidades",
        lastActive: "Hace 5 días (Sesión terminada)"
    },
];

function UsuariosPage() {
    const [users, setUsers] = useState(initialUsers);
    const [search, setSearch] = useState("");
    const [roleFilter, setRoleFilter] = useState("Todos");
    const [statusFilter, setStatusFilter] = useState("Todos");

    // Modals state
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState<typeof initialUsers[0] | null>(null);

    // Form state for creating user
    const [newUserName, setNewUserName] = useState("");
    const [newUserEmail, setNewUserEmail] = useState("");
    const [newUserRole, setNewUserRole] = useState("Revisor Académico");
    const [newUserDept, setNewUserDept] = useState("Facultad de Ingeniería");
    const [newUserPerms, setNewUserPerms] = useState<string[]>(["Aprobación de metadatos", "Ver monitoreo y alertas"]);

    // Available permissions list
    const availablePermissions = [
        "Gestión total del sistema",
        "Crear/Revocar usuarios",
        "Aprobación de metadatos",
        "Sugerencias agente de IA",
        "Sincronización de metadatos",
        "Configuración LLM",
        "Ver monitoreo y alertas",
        "Análisis documental PDF",
        "Ver auditoría",
        "Exportar reportes de calidad",
    ];

    const handleCreateUser = (e: React.FormEvent) => {
        e.preventDefault();
        if (!newUserName || !newUserEmail) return;
        const newUser = {
            id: `USR-00${users.length + 1}`,
            name: newUserName,
            email: newUserEmail,
            role: newUserRole,
            status: "Activo" as const,
            permissions: newUserPerms.length > 0 ? newUserPerms : ["Ver monitoreo y alertas"],
            department: newUserDept,
            lastActive: "Registrado recién"
        };
        setUsers([newUser, ...users]);
        setIsCreateModalOpen(false);
        setNewUserName("");
        setNewUserEmail("");
    };

    const handleToggleRevoke = (id: string) => {
        setUsers(users.map(u => {
            if (u.id === id) {
                return {
                    ...u,
                    status: u.status === "Activo" ? "Revocado" : "Activo",
                    lastActive: u.status === "Activo" ? "Permiso revocado por admin" : "Reactivado hoy"
                };
            }
            return u;
        }));
    };

    const handleSaveEdit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingUser) return;
        setUsers(users.map(u => u.id === editingUser.id ? editingUser : u));
        setEditingUser(null);
    };

    const togglePermissionInList = (perm: string, list: string[], setList: (l: string[]) => void) => {
        if (list.includes(perm)) {
            setList(list.filter(p => p !== perm));
        } else {
            setList([...list, perm]);
        }
    };

    const filteredUsers = users.filter(u => {
        const matchSearch = u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase()) || u.id.toLowerCase().includes(search.toLowerCase());
        const matchRole = roleFilter === "Todos" || u.role.includes(roleFilter);
        const matchStatus = statusFilter === "Todos" || u.status === statusFilter;
        return matchSearch && matchRole && matchStatus;
    });

    return (
        <div className="h-full overflow-y-auto space-y-6">
            <SectionHeader
                title="Gestión de Usuarios y Control de Permisos"
                description="Panel administrativo para crear nuevos usuarios, asignar o modificar roles y revocar privilegios de acceso al sistema."
            />

            {/* Stats bar */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                    { label: "Total usuarios del sistema", value: users.length, color: "#1565C0", icon: Users },
                    { label: "Permisos activos", value: users.filter(u => u.status === "Activo").length, color: "#00aea7", icon: UserCheck },
                    { label: "Accesos revocados", value: users.filter(u => u.status === "Revocado").length, color: "#d32f2f", icon: UserX },
                ].map((s, idx) => {
                    const Icon = s.icon;
                    return (
                        <Card key={idx} className="p-4 flex items-center justify-between border border-gray-100 bg-white">
                            <div>
                                <p className="text-[11px] text-[#6b7a90] mb-1 font-medium">{s.label}</p>
                                <p className="text-2xl font-bold" style={{ color: s.color }}>{s.value}</p>
                            </div>
                            <div className="w-11 h-11 rounded-xl flex items-center justify-center bg-gray-50 text-gray-600">
                                <Icon size={20} style={{ color: s.color }} />
                            </div>
                        </Card>
                    );
                })}
            </div>

            <Card>
                {/* Toolbar */}
                <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-gray-50 bg-slate-50/40">
                    <div className="flex items-center gap-3 flex-1 min-w-[280px]">
                        <div className="relative flex-1 max-w-xs">
                            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7a90]" />
                            <input
                                type="text"
                                placeholder="Buscar por nombre, correo o ID..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
                            />
                        </div>
                        <div className="flex gap-1">
                            {["Todos", "Activo", "Revocado"].map((f) => (
                                <button
                                    key={f}
                                    onClick={() => setStatusFilter(f)}
                                    className="px-3 py-1.5 text-xs rounded-lg font-medium transition-all"
                                    style={{
                                        background: statusFilter === f ? "#00aea7" : "#f0f4f8",
                                        color: statusFilter === f ? "#fff" : "#6b7a90",
                                    }}
                                >
                                    {f}
                                </button>
                            ))}
                        </div>
                    </div>

                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-[#00aea7] hover:bg-[#009b95] rounded-xl shadow-sm shadow-[#00aea7]/20 transition-all cursor-pointer"
                    >
                        <UserPlus size={15} />
                        Crear Usuario y Asignar Permiso
                    </button>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-100 bg-slate-50/80">
                                {["Usuario / Correo", "Rol & Departamento", "Permisos Asignados", "Estado", "Última Actividad", "Acciones"].map((h) => (
                                    <th key={h} className="text-left px-4 py-3.5 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide">
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filteredUsers.map((u) => (
                                <tr key={u.id} className={`border-b border-gray-50 transition-colors ${u.status === "Revocado" ? "bg-red-50/20" : "hover:bg-gray-50/50"}`}>
                                    <td className="px-4 py-3.5">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs ${u.status === "Revocado" ? "bg-red-100 text-red-700" : "bg-[#00aea7]/10 text-[#00aea7]"}`}>
                                                {u.name.split(" ").map(n => n[0]).slice(0, 2).join("")}
                                            </div>
                                            <div>
                                                <p className="text-xs font-bold text-[#1a2332]">{u.name}</p>
                                                <p className="text-[11px] text-[#6b7a90]">{u.email}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3.5">
                                        <p className="text-xs font-medium text-[#1a2332]">{u.role}</p>
                                        <p className="text-[11px] text-[#6b7a90]">{u.department}</p>
                                    </td>
                                    <td className="px-4 py-3.5 max-w-xs">
                                        <div className="flex flex-wrap gap-1">
                                            {u.permissions.slice(0, 2).map((p, i) => (
                                                <span key={i} className="text-[10px] font-medium px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md border border-slate-200/60">
                                                    {p}
                                                </span>
                                            ))}
                                            {u.permissions.length > 2 && (
                                                <span className="text-[10px] font-semibold px-1.5 py-0.5 bg-teal-50 text-teal-700 rounded-md border border-teal-200">
                                                    +{u.permissions.length - 2} más
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3.5">
                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${u.status === "Activo" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
                                            <span className={`w-1.5 h-1.5 rounded-full ${u.status === "Activo" ? "bg-emerald-500" : "bg-red-500"}`} />
                                            {u.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3.5 text-xs text-[#6b7a90]">{u.lastActive}</td>
                                    <td className="px-4 py-3.5">
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => setEditingUser(u)}
                                                title="Modificar permisos y roles"
                                                className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-gray-200 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition-colors cursor-pointer"
                                            >
                                                <Key size={13} className="text-[#00aea7]" />
                                                Modificar
                                            </button>
                                            <button
                                                onClick={() => handleToggleRevoke(u.id)}
                                                title={u.status === "Activo" ? "Revocar acceso" : "Reactivar acceso"}
                                                className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg border transition-colors cursor-pointer ${u.status === "Activo" ? "text-red-600 border-red-200 bg-red-50/40 hover:bg-red-50" : "text-emerald-700 border-emerald-200 bg-emerald-50/40 hover:bg-emerald-50"}`}
                                            >
                                                {u.status === "Activo" ? (
                                                    <>
                                                        <UserX size={13} /> Revocar
                                                    </>
                                                ) : (
                                                    <>
                                                        <UserCheck size={13} /> Reactivar
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </Card>

            {/* Modal Crear Usuario */}
            {isCreateModalOpen && (
                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full border border-gray-100 overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-slate-50/50">
                            <div className="flex items-center gap-2.5">
                                <div className="w-9 h-9 rounded-xl bg-[#00aea7]/10 text-[#00aea7] flex items-center justify-center font-bold">
                                    <UserPlus size={18} />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-slate-800">Crear Usuario y Permisos</h3>
                                    <p className="text-[11px] text-slate-500">Asigne un nuevo rol institucional al sistema</p>
                                </div>
                            </div>
                            <button onClick={() => setIsCreateModalOpen(false)} className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg">
                                <X size={18} />
                            </button>
                        </div>

                        <form onSubmit={handleCreateUser} className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs font-semibold text-slate-700 block mb-1">Nombre Completo</label>
                                    <input
                                        type="text"
                                        required
                                        placeholder="Ej: Carlos Fuentes"
                                        value={newUserName}
                                        onChange={(e) => setNewUserName(e.target.value)}
                                        className="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-slate-700 block mb-1">Correo Institucional</label>
                                    <input
                                        type="email"
                                        required
                                        placeholder="carlos.fuentes@usach.cl"
                                        value={newUserEmail}
                                        onChange={(e) => setNewUserEmail(e.target.value)}
                                        className="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs font-semibold text-slate-700 block mb-1">Rol Asignado</label>
                                    <select
                                        value={newUserRole}
                                        onChange={(e) => setNewUserRole(e.target.value)}
                                        className="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
                                    >
                                        <option value="Administrador">Administrador</option>
                                        <option value="Curador">Curador</option>
                                        <option value="Perfil académico">Perfil académico</option>
                                        <option value="Usuario externo">Usuario externo</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-slate-700 block mb-1">Departamento / Unidad</label>
                                    <input
                                        type="text"
                                        required
                                        value={newUserDept}
                                        onChange={(e) => setNewUserDept(e.target.value)}
                                        className="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="text-xs font-semibold text-slate-700 block mb-2">Asignar Permisos Funcionales</label>
                                <div className="grid grid-cols-2 gap-2 p-3 bg-slate-50/80 rounded-xl border border-gray-100 max-h-48 overflow-y-auto">
                                    {availablePermissions.map((perm) => (
                                        <label key={perm} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer p-1.5 rounded hover:bg-white transition-colors">
                                            <input
                                                type="checkbox"
                                                checked={newUserPerms.includes(perm)}
                                                onChange={() => togglePermissionInList(perm, newUserPerms, setNewUserPerms)}
                                                className="rounded text-[#00aea7] focus:ring-[#00aea7] accent-[#00aea7]"
                                            />
                                            <span className="truncate">{perm}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <div className="pt-2 flex items-center justify-end gap-2 border-t border-gray-100">
                                <button
                                    type="button"
                                    onClick={() => setIsCreateModalOpen(false)}
                                    className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-[#00aea7] hover:bg-[#009b95] rounded-xl shadow-sm transition-all cursor-pointer"
                                >
                                    <Plus size={14} /> Crear Usuario
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal Modificar Permisos */}
            {editingUser && (
                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full border border-gray-100 overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-slate-50/50">
                            <div className="flex items-center gap-2.5">
                                <div className="w-9 h-9 rounded-xl bg-teal-500/10 text-teal-600 flex items-center justify-center font-bold">
                                    <Key size={18} />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-slate-800">Modificar Permisos</h3>
                                    <p className="text-[11px] text-slate-500">{editingUser.name} ({editingUser.email})</p>
                                </div>
                            </div>
                            <button onClick={() => setEditingUser(null)} className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg">
                                <X size={18} />
                            </button>
                        </div>

                        <form onSubmit={handleSaveEdit} className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
                            <div>
                                <label className="text-xs font-semibold text-slate-700 block mb-1">Cambiar Rol del Usuario</label>
                                <select
                                    value={editingUser.role}
                                    onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value as any })}
                                    className="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
                                >
                                    <option value="Administrador">Administrador</option>
                                    <option value="Curador">Curador</option>
                                    <option value="Perfil académico">Perfil académico</option>
                                    <option value="Usuario externo">Usuario externo</option>
                                </select>
                            </div>

                            <div>
                                <label className="text-xs font-semibold text-slate-700 block mb-2">Permisos Asignados actualmente</label>
                                <div className="grid grid-cols-2 gap-2 p-3 bg-slate-50/80 rounded-xl border border-gray-100 max-h-56 overflow-y-auto">
                                    {availablePermissions.map((perm) => (
                                        <label key={perm} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer p-1.5 rounded hover:bg-white transition-colors">
                                            <input
                                                type="checkbox"
                                                checked={editingUser.permissions.includes(perm)}
                                                onChange={() => {
                                                    const perms = editingUser.permissions;
                                                    const newPerms = perms.includes(perm) ? perms.filter(p => p !== perm) : [...perms, perm];
                                                    setEditingUser({ ...editingUser, permissions: newPerms });
                                                }}
                                                className="rounded text-[#00aea7] focus:ring-[#00aea7] accent-[#00aea7]"
                                            />
                                            <span className="truncate">{perm}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <div className="pt-2 flex items-center justify-between border-t border-gray-100">
                                <span className="text-[11px] text-slate-400">Estado actual: <strong className={editingUser.status === "Activo" ? "text-emerald-600" : "text-red-600"}>{editingUser.status}</strong></span>
                                <div className="flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setEditingUser(null)}
                                        className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                                    >
                                        Cancelar
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-[#00aea7] hover:bg-[#009b95] rounded-xl shadow-sm transition-all cursor-pointer"
                                    >
                                        Guardar Cambios
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── LoginPage ────────────────────────────────────────────────────────────────
function LoginPage({ onLogin }: { onLogin: () => void }) {
    const [email, setEmail] = useState("admin.vriic@usach.cl");
    const [password, setPassword] = useState("••••••••••••");
    const [remember, setRemember] = useState(true);
    const [error, setError] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!email || !password) {
            setError("Por favor ingrese su correo y contraseña");
            return;
        }
        onLogin();
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-[#F7F9FB] p-4" style={{ fontFamily: "'Inter', sans-serif" }}>
            <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl overflow-hidden grid grid-cols-1 md:grid-cols-12 border border-gray-100">
                <div className="md:col-span-5 p-8 flex flex-col justify-between relative overflow-hidden text-white" style={{ background: "linear-gradient(135deg, #00aea7 0%, #007a75 100%)" }}>
                    <div className="absolute -right-10 -top-10 w-40 h-40 rounded-full bg-white/10 blur-xl pointer-events-none" />
                    <div className="absolute -left-10 -bottom-10 w-40 h-40 rounded-full bg-black/10 blur-xl pointer-events-none" />

                    <div className="relative z-10 flex items-center gap-3">
                        <div className="w-full h-24 rounded-xl bg-[#00aea7] p-3 shadow-md flex items-center justify-center flex-shrink-0">
                            <img src="/logo-usach.png" alt="Escudo USACH" className="w-full h-full object-contain" />
                        </div>
                    </div>
                    <div className="translate-y-3">
                        <span className="text-xs font-semibold tracking-wider uppercase block text-white/80">VRIIC · USACH</span>
                        <span className="text-sm font-bold block leading-tight">DSpace-CRIS</span>
                    </div>

                    <div className="relative z-10 my-8">
                        <h1 className="text-2xl font-bold leading-tight mb-3">Agente Inteligente para el Enriquecimiento de Metadatos</h1>
                        <p className="text-xs text-white/85 leading-relaxed">
                            Plataforma para el enriquecimiento de metadatos de publicaciones científicas institucionales
                        </p>
                    </div>

                    <div className="relative z-10 mt-8">
                        <h1 className="text-xs font-bold leading-tight mb-3">Agradecimiento</h1>
                        <p className="text-xs text-white/85 leading-relaxed">
                            El presente trabajo fue desarrollado gracias al proyecto INCAR250006, financiado por ANID.
                        </p>
                    </div>

                    <div className="relative z-10 pt-6 border-t border-white/20 flex items-center justify-between text-[11px] text-white/75">
                        <span>Universidad de Santiago de Chile</span>
                        <span>Acceso Seguro</span>
                    </div>
                </div>

                <div className="md:col-span-7 p-8 md:p-10 flex flex-col justify-center">
                    <div className="flex items-center gap-4 -mt-3 mb-3">
                        <div className="h-13 w-full rounded-xl p-1.5 flex items-center justify-center">
                            <img src="/image-vriic.png" alt="Logo VRIIC" className="w-full h-full object-contain brightness-0" />
                        </div>
                        <div className="h-13 w-full rounded-xl p-1.5 flex items-center justify-center">
                            <img src="/anid.png" alt="Logo ANID" className="w-full h-full object-contain brightness-0" />
                        </div>
                    </div>

                    <div className="mb-6 flex items-center gap-4">

                        <div>
                            <h2 className="text-xl font-bold text-[#1a2332]">Iniciar Sesión</h2>
                            <p className="text-xs text-[#6b7a90] mt-1">Ingresa con tus credenciales para acceder al sistema.</p>
                        </div>
                    </div>

                    {error && (
                        <div className="mb-4 p-3 rounded-lg bg-[#ffebee] border border-[#ffcdd2] text-[#d32f2f] text-xs flex items-center gap-2">
                            <AlertCircle size={15} />
                            <span>{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                        <div>
                            <label className="text-xs font-semibold text-[#1a2332] mb-1.5 block">Correo institucional</label>
                            <div className="relative">
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-[#1a2332] focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7] transition-all"
                                    placeholder="ejemplo@usach.cl"
                                    required
                                />
                                <User size={16} className="absolute left-3 top-2.5 text-[#6b7a90]" />
                            </div>
                        </div>

                        <div>
                            <label className="text-xs font-semibold text-[#1a2332] mb-1.5 block">Contraseña</label>
                            <div className="relative">
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-[#1a2332] focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7] transition-all"
                                    placeholder="••••••••••••"
                                    required
                                />
                                <ShieldCheck size={16} className="absolute left-3 top-2.5 text-[#6b7a90]" />
                            </div>
                        </div>

                        <div className="flex items-center justify-between mt-1">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={remember}
                                    onChange={(e) => setRemember(e.target.checked)}
                                    className="rounded text-[#00aea7] focus:ring-[#00aea7] accent-[#00aea7]"
                                />
                                <span className="text-xs text-[#6b7a90]">Recordar sesión</span>
                            </label>
                            <a href="#olvido" onClick={(e) => { e.preventDefault(); alert("Por favor contacte al soporte de VRIIC para restablecer sus credenciales."); }} className="text-xs font-medium text-[#00aea7] hover:underline">
                                ¿Olvidaste tu contraseña?
                            </a>
                        </div>

                        <button
                            type="submit"
                            className="mt-2 w-full py-2.5 px-4 rounded-lg text-white font-medium text-xs flex items-center justify-center gap-2 shadow-md hover:opacity-95 transition-all cursor-pointer"
                            style={{ background: "#00aea7" }}
                        >
                            <span>Acceder al Sistema</span>
                            <ArrowRight size={16} />
                        </button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-gray-100 text-center">
                        <p className="text-[11px] text-[#6b7a90]">
                            Al ingresar, aceptas las políticas de seguridad y uso de datos institucionales de la Universidad de Santiago de Chile.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ─── App Shell ────────────────────────────────────────────────────────────────
export default function App() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [page, setPage] = useState<Page>("dashboard");
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

    if (!isLoggedIn) {
        return (
            <LoginPage
                onLogin={() => {
                    setIsLoggedIn(true);
                    setPage("dashboard");
                }}
            />
        );
    }

    const renderPage = () => {
        switch (page) {
            case "dashboard": return <DashboardPage onNav={setPage} />;
            case "monitoreo": return <MonitoreoPage />;
            case "recuperacion": return <ReportesPage />;
            case "analisis": return <AnalisisPage />;
            case "validacion": return <ValidacionPage />;
            case "aprobacion": return <AprobacionPage />;
            case "auditoria": return <AuditoriaPage />;
            case "reportes": return <ReportesPage />;
            case "usuarios": return <UsuariosPage />;
            case "configuracion": return <ConfiguracionPage />;
            case "perfil": return <PerfilPage />;
            default: return <DashboardPage onNav={setPage} />;
        }
    };

    return (
        <div className="flex h-screen overflow-hidden" style={{ fontFamily: "'Inter', sans-serif", background: "#F7F9FB" }}>
            <Sidebar current={page} onNav={setPage} collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />

            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <Header page={page} onLogout={() => setIsLoggedIn(false)} />
                <main className="flex-1 overflow-hidden p-6">
                    {renderPage()}
                </main>
            </div>
        </div>
    );
}
