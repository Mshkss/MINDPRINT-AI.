"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  MessageCircle,
  BookOpen,
  Leaf,
  ShieldCheck,
  Users,
  LogOut,
  ArrowLeftRight,
  ChevronRight,
  Menu,
  X,
  Sparkles,
  Flower2,
  ArrowRight,
} from "lucide-react";
import { toast } from "sonner";
import { api, User } from "@/lib/api";
import { Logo, Loading, Badge } from "./common";
import { Button } from "./ui/button";
import { Landing } from "./landing";
import { PatientDashboard, Journal, Exercises, Privacy } from "./patient";
import { Chat } from "./chat";
import { PsychDashboard, PatientDetail } from "./psychologist";
export function Platform() {
  const path = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [config, setConfig] = useState<{
    demo_mode: boolean;
    ai_provider: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [menu, setMenu] = useState(false);
  useEffect(() => {
    api<{ demo_mode: boolean; ai_provider: string }>("/config")
      .then(setConfig)
      .catch(() => {});
  }, []);
  useEffect(() => {
    setMenu(false);
    if (path === "/" || path === "/login") {
      setLoading(false);
      return;
    }
    let live = true;
    setError("");
    api<User>("/me")
      .then((u) => {
        if (live) {
          setUser(u);
          const area = path.split("/")[1];
          if (
            ["patient", "psychologist", "admin"].includes(area) &&
            area !== u.role
          )
            router.replace("/" + u.role + "/dashboard");
        }
      })
      .catch((e) => {
        if (live) {
          if (e.message === "Войдите в аккаунт") router.replace("/login");
          else setError(e.message);
        }
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [path, router]);
  async function demo(role: "patient" | "psychologist") {
    try {
      const u = await api<User>("/auth/demo", "POST", { role });
      setUser(u);
      router.push("/" + role + "/dashboard");
    } catch (e) {
      toast.error((e as Error).message);
    }
  }
  if (path === "/") return <Landing />;
  if (path === "/login")
    return (
      <div className="login-page">
        <Link href="/">
          <Logo />
        </Link>
        <div className="login-card card">
          <span className="login-flower">
            <Flower2 size={36} />
          </span>
          <h1>
            Ваше пространство
            <br />
            для важных изменений.
          </h1>
          <p>Рады видеть вас в MINDPRINT</p>
          {config?.demo_mode && (
            <div className="demo-logins">
              <Badge>Синтетические данные · демоверсия</Badge>
              <Button onClick={() => demo("patient")}>
                Войти как пациент <ArrowRight size={16} />
              </Button>
              <Button variant="secondary" onClick={() => demo("psychologist")}>
                Войти как психолог <ArrowRight size={16} />
              </Button>
              <div className="divider">или войти по email</div>
            </div>
          )}
          <form
            className="form-stack"
            onSubmit={async (e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              try {
                const u = await api<User>(
                  "/auth/login",
                  "POST",
                  Object.fromEntries(f),
                );
                setUser(u);
                router.push("/" + u.role + "/dashboard");
              } catch (e) {
                toast.error((e as Error).message);
              }
            }}
          >
            <label>
              Email
              <input
                name="email"
                type="email"
                required
                placeholder="you@example.ru"
              />
            </label>
            <label>
              Пароль
              <input
                name="password"
                type="password"
                required
                autoComplete="current-password"
              />
            </label>
            <Button type="submit" variant="secondary">
              Войти
            </Button>
          </form>
          <small>Не является службой экстренной психологической помощи.</small>
        </div>
      </div>
    );
  if (loading || !user)
    return (
      <main className="main-content">
        {error ? (
          <div className="card">
            <h2>Не удалось загрузить кабинет</h2>
            <p>{error}</p>
            <Button onClick={() => location.reload()}>Повторить</Button>
          </div>
        ) : (
          <Loading />
        )}
      </main>
    );
  const patient = user.role === "patient";
  const nav = patient
    ? ([
        ["/patient/dashboard", "Моё пространство", LayoutDashboard],
        ["/patient/chat", "ИИ-компаньон", MessageCircle],
        ["/patient/journal", "Дневник", BookOpen],
        ["/patient/exercises", "Мои упражнения", Leaf],
        ["/patient/privacy", "Приватность", ShieldCheck],
      ] as const)
    : ([
        ["/psychologist/dashboard", "Обзор", LayoutDashboard],
        ["/psychologist/patients", "Мои пациенты", Users],
      ] as const);
  return (
    <div className="app-layout">
      <aside className={"sidebar " + (menu ? "open" : "")}>
        <Link className="sidebar-logo" href="/">
          <Logo />
        </Link>
        <div className="workspace-label">
          {patient ? "ЛИЧНОЕ ПРОСТРАНСТВО" : "КАБИНЕТ ПСИХОЛОГА"}
        </div>
        <nav>
          {nav.map(([href, label, Icon]) => (
            <Link
              href={href}
              key={href}
              className={
                path === href ||
                (href.endsWith("patients") && path.startsWith(href))
                  ? "active"
                  : ""
              }
            >
              <Icon size={19} />
              {label}
              {path === href && <span className="nav-dot" />}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="care-note">
            <Sparkles size={21} />
            <h4>
              Маленькие шаги
              <br />
              имеют значение
            </h4>
            <p>
              {patient
                ? "Дайте себе время. Мы рядом на этом пути."
                : "Технологии помогают. Человек остаётся в центре."}
            </p>
          </div>
          <div className="account">
            <span className="avatar">{user.name[0]}</span>
            <div>
              <b>{user.name}</b>
              <small>{patient ? "Моё пространство" : "Психолог"}</small>
            </div>
            <button
              className="icon-button"
              aria-label="Выйти"
              onClick={async () => {
                await api("/auth/logout", "POST");
                setUser(null);
                router.push("/login");
              }}
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      {menu && (
        <div className="sidebar-backdrop" onClick={() => setMenu(false)} />
      )}
      <div className="app-body">
        <header className="topbar">
          <div className="row">
            <button
              className="icon-button mobile-menu"
              aria-label="Открыть меню"
              onClick={() => setMenu(!menu)}
            >
              {menu ? <X /> : <Menu />}
            </button>
            <span>{patient ? "Моё пространство" : "Рабочее пространство"}</span>
            <ChevronRight size={14} />
            <b>
              {nav.find(([href]) => href === path)?.[1] || "Профиль пациента"}
            </b>
          </div>
          <div className="row">
            {config?.demo_mode && (
              <>
                <span className="demo-pill">
                  <span className="status-dot" /> Демо ·{" "}
                  {config.ai_provider === "mock"
                    ? "автономный режим"
                    : config.ai_provider}
                </span>
                <button
                  className="switch-role"
                  onClick={() => demo(patient ? "psychologist" : "patient")}
                >
                  <ArrowLeftRight size={15} />
                  <span>
                    {patient ? "Кабинет психолога" : "Кабинет пациента"}
                  </span>
                </button>
              </>
            )}
          </div>
        </header>
        <main className="main-content" key={path}>
          {path === "/patient/dashboard" ? (
            <PatientDashboard user={user} />
          ) : path === "/patient/chat" ? (
            <Chat />
          ) : path === "/patient/journal" ? (
            <Journal />
          ) : path === "/patient/exercises" ? (
            <Exercises />
          ) : path === "/patient/privacy" ? (
            <Privacy />
          ) : path === "/psychologist/dashboard" ||
            path === "/psychologist/patients" ? (
            <PsychDashboard user={user} />
          ) : path.startsWith("/psychologist/patients/") ? (
            <PatientDetail id={Number(path.split("/").at(-1))} />
          ) : path === "/admin/dashboard" ? (
            <Admin />
          ) : (
            <div className="card">
              <h1>Страница не найдена</h1>
              <Link href={"/" + user.role + "/dashboard"}>
                Вернуться в кабинет
              </Link>
            </div>
          )}
        </main>
        <div className="app-footer">
          <span>
            <ShieldCheck size={13} /> Ваши данные — под вашим контролем
          </span>
          <span>MINDPRINT AI · Пространство заботы</span>
        </div>
      </div>
    </div>
  );
}
function Admin() {
  const [stats, setStats] = useState<{
    total: number;
    by_role: Record<string, number>;
    target: number;
  }>();
  useEffect(() => {
    api<typeof stats>("/waitlist/stats")
      .then(setStats)
      .catch((e) => toast.error(e.message));
  }, []);
  return (
    <div className="card">
      <h1>Лист ожидания</h1>
      <h2>{stats?.total ?? "…"} / 100</h2>
      <p>Уникальные регистрации</p>
      <pre>{JSON.stringify(stats?.by_role, null, 2)}</pre>
    </div>
  );
}
