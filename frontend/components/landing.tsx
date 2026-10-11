"use client";
import Link from "next/link";
import { useState } from "react";
import {
  ArrowRight,
  Check,
  ShieldCheck,
  Sparkles,
  Heart,
  CircleDot,
  ArrowUpRight,
} from "lucide-react";
import { toast } from "sonner";
import { Logo, Badge } from "./common";
import { Button } from "./ui/button";
import { api } from "@/lib/api";
export function Landing() {
  const [busy, setBusy] = useState(false);
  return (
    <div className="landing">
      <nav className="landing-nav">
        <Link href="/">
          <Logo />
        </Link>
        <div className="landing-links">
          <a href="#how">Как это работает</a>
          <a href="#psychologists">Для психологов</a>
          <Link href="/login">
            Войти <ArrowUpRight size={15} />
          </Link>
        </div>
      </nav>
      <main>
        <section className="hero">
          <div className="hero-copy">
            <Badge>
              <span className="status-dot" /> Рядом между встречами
            </Badge>
            <h1>
              167 часов между
              <br />
              консультациями.
              <br />
              <span>Ни один не должен оставаться без поддержки.</span>
            </h1>
            <p>
              Ни один час не должен оставаться без поддержки. Персональный
              ИИ-компаньон помогает вам между сеансами, а психологу — лучше
              понимать вашу динамику.
            </p>
            <div className="row wrap">
              <Button asChild>
                <Link href="/login">
                  Попробовать демо <ArrowRight size={17} />
                </Link>
              </Button>
              <Button asChild variant="secondary">
                <a href="#psychologists">Для психологов</a>
              </Button>
            </div>
            <div className="hero-note">
              <ShieldCheck size={15} /> Вы решаете, чем делиться с психологом
            </div>
          </div>
          <div className="hero-visual">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="preview-card">
              <div className="row between">
                <div className="row">
                  <span className="avatar">А</span>
                  <div>
                    <b>Моё пространство</b>
                    <small>Маленькие шаги. Важные изменения.</small>
                  </div>
                </div>
                <Sparkles color="#8578db" />
              </div>
              <div className="preview-greeting">Как ты сегодня?</div>
              <div className="preview-moods">
                😣 <span>😔</span> 😐 <span className="selected">🙂</span> 😄
              </div>
              <div className="mini-chart">
                <svg
                  viewBox="0 0 400 120"
                  role="img"
                  aria-label="Иллюстрация графика настроения"
                >
                  <path
                    d="M0 100 Q40 90 65 95 T130 60 T195 75 T260 38 T325 45 T400 10"
                    fill="none"
                    stroke="#8c7be8"
                    strokeWidth="4"
                  />
                  <path
                    d="M0 100 Q40 90 65 95 T130 60 T195 75 T260 38 T325 45 T400 10 L400 120 L0 120Z"
                    fill="#efecfc"
                  />
                </svg>
              </div>
              <div className="preview-message">
                <Sparkles size={21} />
                <p>
                  Можно начать с того, что сейчас чувствуешь.
                  <br />
                  <b>Я здесь, чтобы выслушать.</b>
                </p>
              </div>
            </div>
            <div className="floating-note">
              <span className="check-circle">
                <Check size={18} />
              </span>
              <div>
                <b>Дневник мыслей</b>
                <small>Один шаг к пониманию себя</small>
              </div>
            </div>
            <span className="illustration-label">Иллюстрация интерфейса</span>
          </div>
        </section>
        <div className="landing-values">
          <span>
            <Heart size={18} /> Поддержка в вашем темпе
          </span>
          <span>
            <CircleDot size={18} /> План вашего психолога
          </span>
          <span>
            <ShieldCheck size={18} /> Контроль над своими данными
          </span>
        </div>
        <section className="landing-section" id="how">
          <div className="eyebrow">НЕПРЕРЫВНЫЙ ПРОЦЕСС</div>
          <h2>
            Между «до встречи»
            <br />и следующей встречей.
          </h2>
          <div className="steps-grid">
            {[
              [
                "01",
                "Ваш личный план",
                "Психолог определяет цели и подбирает упражнения.",
              ],
              [
                "02",
                "Пространство для себя",
                "Вы общаетесь с ИИ, ведёте дневник и замечаете чувства.",
              ],
              [
                "03",
                "Изменения становятся видимыми",
                "Система собирает динамику и указывает основания наблюдений.",
              ],
              [
                "04",
                "Более осмысленная встреча",
                "Психолог изучает сводку и корректирует план вместе с вами.",
              ],
            ].map(([n, t, d]) => (
              <div key={n}>
                <span>{n}</span>
                <h3>{t}</h3>
                <p>{d}</p>
              </div>
            ))}
          </div>
        </section>
        <section className="psych-section" id="psychologists">
          <div>
            <div className="eyebrow">ДЛЯ ПСИХОЛОГОВ</div>
            <h2>
              Больше контекста.
              <br />
              Ближе к человеку.
            </h2>
            <p>
              Вы управляете планом сопровождения. ИИ помогает выполнять
              назначенные упражнения и превращает записи в наблюдения с
              проверяемыми источниками.
            </p>
            <Link href="/login">
              Открыть кабинет психолога <ArrowRight size={17} />
            </Link>
          </div>
          <div className="feature-list">
            {[
              "Индивидуальные цели и разрешённые сценарии",
              "Динамика по сохранённым записям",
              "Обратная связь по каждому AI-наблюдению",
              "Архитектура для локального развёртывания",
            ].map((x) => (
              <div key={x}>
                <Check size={18} />
                {x}
              </div>
            ))}
          </div>
        </section>
        <section className="waitlist" id="waitlist">
          <div>
            <Badge>Ранний доступ</Badge>
            <h2>Начнём с маленького шага?</h2>
            <p>Оставьте заявку, чтобы узнать о запуске MINDPRINT AI.</p>
          </div>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              const f = new FormData(e.currentTarget);
              try {
                await api("/waitlist", "POST", Object.fromEntries(f));
                toast.success("Спасибо! Ваша заявка принята.");
                (e.target as HTMLFormElement).reset();
              } catch (e) {
                toast.error((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <label>
              Имя
              <input
                name="name"
                required
                maxLength={120}
                placeholder="Как к вам обращаться"
              />
            </label>
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
              Мне интересно как
              <select name="role">
                <option value="patient">Потенциальному пользователю</option>
                <option value="psychologist">Психологу</option>
              </select>
            </label>
            <Button disabled={busy}>
              {busy ? "Сохраняем…" : "Присоединиться"} <ArrowRight size={16} />
            </Button>
            <small>
              Отправляя форму, вы разрешаете сохранить имя и email для связи о
              запуске.
            </small>
          </form>
        </section>
      </main>
      <footer>
        <Logo />
        <p>ИИ-компаньон, не замена психолога и не служба экстренной помощи.</p>
        <span>© 2026 MINDPRINT</span>
      </footer>
    </div>
  );
}
