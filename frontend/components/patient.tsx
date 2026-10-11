"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Sparkles,
  Leaf,
  Check,
  Plus,
  Clock,
  BookOpen,
  ShieldCheck,
  Heart,
  Play,
  Pause,
} from "lucide-react";
import { toast } from "sonner";
import {
  api,
  Patient,
  User,
  Analytics,
  Assignment,
  Entry,
  Consent,
  date,
} from "@/lib/api";
import { Heading, Badge, MoodChart, Metric, Loading, Empty } from "./common";
import { Button } from "./ui/button";
import { Modal } from "./ui/dialog";
export const moods = [
  ["😣", "Очень плохо"],
  ["😔", "Плохо"],
  ["😐", "Нормально"],
  ["🙂", "Хорошо"],
  ["😄", "Отлично"],
];
function useData<T>(path: string) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let live = true;
    api<T>(path)
      .then((d) => {
        if (live) {
          setData(d);
          setError("");
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [path, version]);
  return { data, setData, error, reload: () => setVersion((v) => v + 1) };
}
export function PatientDashboard({ user }: { user: User }) {
  const { data, reload, error } = useData<Analytics>(
    "/analytics/" + user.id + "?days=7",
  );
  const { data: profile } = useData<Patient>("/patients/" + user.id);
  const { data: exercises, reload: reloadExercises } =
    useData<Assignment[]>("/exercises");
  const [saving, setSaving] = useState(false);
  const [selected, setSelected] = useState<number>();
  const [active, setActive] = useState<Assignment | null>(null);
  if (error) return <p role="alert">{error}</p>;
  return (
    <>
      <Heading
        eyebrow="МЕСТО, ГДЕ МОЖНО БЫТЬ СОБОЙ"
        title={`Привет, ${user.name}`}
        subtitle="Не обязательно успевать всё. Начните с себя."
        actions={
          <span className="today">
            {new Date().toLocaleDateString("ru-RU", {
              day: "numeric",
              month: "long",
              weekday: "long",
            })}
          </span>
        }
      />
      {profile?.plan?.reminders_enabled &&
        exercises?.some((a) => a.available) && (
          <div className="reminder-note">
            <Clock size={17} />
            <span>
              {profile.plan.reminder_frequency === "weekly"
                ? "Напоминание на эту неделю"
                : "Напоминание на сегодня"}
              : в вашем плане есть упражнения. Выберите удобный момент.
            </span>
            <Link href="/patient/exercises">Открыть</Link>
          </div>
        )}
      <section className="mood-checkin card">
        <div>
          <Badge tone="green">
            <Heart size={12} /> Время для себя
          </Badge>
          <h2>Как ты себя чувствуешь сегодня?</h2>
          <p>Любое чувство заслуживает внимания.</p>
        </div>
        <div className="mood-options">
          {moods.map(([emoji, label], i) => (
            <button
              disabled={saving}
              aria-label={label}
              key={label}
              className={selected === i + 1 ? "selected" : ""}
              onClick={async () => {
                setSaving(true);
                try {
                  await api("/journal", "POST", {
                    mood_score: i + 1,
                    content: "",
                  });
                  setSelected(i + 1);
                  reload();
                  toast.success("Настроение сохранено");
                } catch (e) {
                  toast.error((e as Error).message);
                } finally {
                  setSaving(false);
                }
              }}
            >
              <span>{emoji}</span>
              <small>{label}</small>
            </button>
          ))}
        </div>
      </section>
      <div className="patient-grid">
        <section className="card">
          <div className="section-title">
            <div>
              <h2>Моё состояние</h2>
              <p>Самооценка настроения за 7 дней</p>
            </div>
            <Badge tone="neutral">Эта неделя</Badge>
          </div>
          {data ? <MoodChart data={data.series} /> : <Loading />}
          <div className="chart-note">
            <span className="legend-dot" /> Настроение{" "}
            <span>1 — очень плохо · 5 — отлично</span>
          </div>
        </section>
        <section className="companion-card">
          <div className="companion-art">
            <span />
            <span />
            <span />
            <Sparkles size={35} />
          </div>
          <Badge>Ваш ИИ-компаньон</Badge>
          <h2>
            Мысли не обязательно
            <br />
            оставлять при себе.
          </h2>
          <p>
            Можно поговорить о том, что волнует, или вместе пройти упражнение.
          </p>
          <Button asChild>
            <Link href="/patient/chat">
              Начать разговор <ArrowUpRight size={18} />
            </Link>
          </Button>
        </section>
        <section className="card">
          <div className="section-title">
            <div>
              <h2>Мои упражнения</h2>
              <p>Небольшие шаги из вашего плана</p>
            </div>
            <Link className="text-link" href="/patient/exercises">
              Все <ArrowRight size={15} />
            </Link>
          </div>
          {exercises?.length ? (
            exercises
              .slice(0, 3)
              .map((a) => (
                <ExerciseRow key={a.id} a={a} onOpen={() => setActive(a)} />
              ))
          ) : (
            <Empty
              title="Назначений пока нет"
              text="Здесь появятся упражнения вашего психолога."
            />
          )}
        </section>
        <section className="card progress-card">
          <span className="soft-icon">
            <Leaf size={23} />
          </span>
          <h2>В своём темпе</h2>
          <div className="progress-number">
            {data?.completed_count ?? "—"}
            <span>упражнений за неделю</span>
          </div>
          <p>Каждый момент, который вы уделили себе, имеет значение.</p>
          <Link href="/patient/journal" className="text-link">
            Записать, что было важным <ArrowRight size={15} />
          </Link>
        </section>
      </div>
      <div className="quiet-note">
        <ShieldCheck size={17} />
        <p>
          Вы сами выбираете, какие данные видит психолог.{" "}
          <Link href="/patient/privacy">Настроить приватность</Link>
        </p>
      </div>
      <ExerciseRunner
        assignment={active}
        onClose={() => setActive(null)}
        onUpdate={() => {
          reload();
          reloadExercises();
        }}
      />
    </>
  );
}
export function ExerciseRow({
  a,
  onOpen,
}: {
  a: Assignment;
  onOpen: () => void;
}) {
  return (
    <button className="exercise-row" onClick={onOpen}>
      <span
        className={"exercise-icon " + (a.status === "completed" ? "done" : "")}
      >
        {a.status === "completed" ? <Check size={19} /> : <Leaf size={19} />}
      </span>
      <span className="grow">
        <b>{a.exercise.name}</b>
        <small>
          {a.status === "completed"
            ? "Завершено"
            : a.status === "in_progress"
              ? `Шаг ${a.answers.length + 1} из ${a.exercise.steps.length}`
              : "Назначено психологом"}
        </small>
      </span>
      <span className="exercise-time">
        {a.exercise.type === "breathing" ? "2 мин" : "5–10 мин"}
      </span>
      <ArrowUpRight size={16} />
    </button>
  );
}
export function Journal() {
  const { data, error, reload } = useData<Entry[]>("/journal");
  const { data: exercises } = useData<Assignment[]>("/exercises");
  const [open, setOpen] = useState(false);
  const [mood, setMood] = useState(3);
  const [busy, setBusy] = useState(false);
  return (
    <>
      <Heading
        eyebrow="ПРОСТРАНСТВО ДЛЯ РЕФЛЕКСИИ"
        title="Эмоциональный дневник"
        subtitle="Замечайте чувства, находите слова, сохраняйте важное."
        actions={
          <Button onClick={() => setOpen(true)}>
            <Plus size={17} /> Новая запись
          </Button>
        }
      />
      <div className="journal-banner">
        <BookOpen size={23} />
        <p>
          Здесь не нужно подбирать правильные слова.
          <br />
          <b>Пишите так, как чувствуете.</b>
        </p>
        <span>Ваш личный ритм</span>
      </div>
      {error ? (
        <p role="alert">{error}</p>
      ) : !data ? (
        <Loading />
      ) : data.length ? (
        <div className="journal-grid">
          {data.map((e) => (
            <article className="card journal-entry" key={e.id}>
              <div className="row between">
                <span className="journal-date">{date(e.created_at)}</span>
                <span
                  className="journal-emoji"
                  title={moods[e.mood_score - 1][1]}
                >
                  {moods[e.mood_score - 1][0]}
                </span>
              </div>
              <p>{e.content || "Отметка настроения без текстовой записи."}</p>
              <div className="row wrap">
                {e.tags.map((t) => (
                  <Badge tone="neutral" key={t}>
                    {t}
                  </Badge>
                ))}
              </div>
              <small className="entry-status">
                {e.analysis_status === "done"
                  ? "Сохранено · анализ выполнен"
                  : "Сохранено · анализ недоступен"}
              </small>
            </article>
          ))}
        </div>
      ) : (
        <Empty title="Начните с первой записи" />
      )}
      <Modal
        open={open}
        onOpenChange={setOpen}
        title="Что было важным сегодня?"
      >
        <form
          className="form-stack"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            const f = new FormData(e.currentTarget);
            try {
              const result = await api<{ warning?: string }>(
                "/journal",
                "POST",
                {
                  mood_score: mood,
                  content: f.get("content"),
                  tags: String(f.get("tags"))
                    .split(",")
                    .map((x) => x.trim())
                    .filter(Boolean),
                  created_at: (String(f.get("date")) ===
                  new Date().toLocaleDateString("en-CA")
                    ? new Date()
                    : new Date(String(f.get("date")) + "T12:00:00")
                  ).toISOString(),
                  completed_exercises: f.getAll("exercises").map(Number),
                },
              );
              toast.success("Запись сохранена");
              if (result.warning) toast.info(result.warning);
              setOpen(false);
              reload();
            } catch (e) {
              toast.error((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Дата
            <input
              name="date"
              type="date"
              required
              max={new Date().toLocaleDateString("en-CA")}
              defaultValue={new Date().toLocaleDateString("en-CA")}
            />
          </label>
          <div className="mood-options compact">
            {moods.map(([emoji, label], i) => (
              <button
                type="button"
                key={label}
                className={mood === i + 1 ? "selected" : ""}
                aria-label={label}
                onClick={() => setMood(i + 1)}
              >
                {emoji}
              </button>
            ))}
          </div>
          <label>
            Ваши мысли
            <textarea
              name="content"
              required
              rows={5}
              maxLength={10000}
              placeholder="Сегодня я чувствую…"
            />
          </label>
          <label>
            Теги через запятую
            <input name="tags" placeholder="Работа, отношения, забота о себе" />
          </label>
          {exercises?.some((a) => a.status === "completed") && (
            <fieldset>
              <legend>Выполненные упражнения</legend>
              {exercises
                .filter((a) => a.status === "completed")
                .map((a) => (
                  <label className="checkbox-row" key={a.id}>
                    <input type="checkbox" name="exercises" value={a.id} />
                    {a.exercise.name}
                  </label>
                ))}
            </fieldset>
          )}
          <Button disabled={busy}>
            {busy ? "Сохраняем…" : "Сохранить запись"}
          </Button>
        </form>
      </Modal>
    </>
  );
}
export function Exercises() {
  const { data, error, reload } = useData<Assignment[]>("/exercises");
  const [active, setActive] = useState<Assignment | null>(null);
  return (
    <>
      <Heading
        eyebrow="НЕБОЛЬШИЕ ШАГИ К СЕБЕ"
        title="Мои упражнения"
        subtitle="Подобраны вашим психологом с учётом плана сопровождения."
      />
      {error ? (
        <p role="alert">{error}</p>
      ) : !data ? (
        <Loading />
      ) : data.length ? (
        <div className="exercise-grid">
          {data.map((a) => (
            <article className="card exercise-card" key={a.id}>
              <div className="row between">
                <span className="soft-icon">
                  <Leaf />
                </span>
                <Badge tone={a.status === "completed" ? "green" : "purple"}>
                  {a.status === "completed"
                    ? "Завершено"
                    : a.status === "in_progress"
                      ? "В процессе"
                      : "Назначено"}
                </Badge>
              </div>
              <h2>{a.exercise.name}</h2>
              <p>{a.exercise.description}</p>
              <div className="row muted">
                <Clock size={14} />
                {a.exercise.type === "breathing"
                  ? "2 минуты"
                  : `${a.exercise.steps.length} шагов · 5–10 минут`}
              </div>
              <Button
                variant="secondary"
                disabled={!a.available && a.status !== "completed"}
                onClick={() => setActive(a)}
              >
                {a.status === "completed"
                  ? "Посмотреть ответы"
                  : a.answers.length
                    ? "Продолжить"
                    : "Начать упражнение"}
                <ArrowRight size={16} />
              </Button>
            </article>
          ))}
        </div>
      ) : (
        <Empty
          title="Назначений пока нет"
          text="Упражнения появятся после согласования плана с психологом."
        />
      )}
      <ExerciseRunner
        assignment={active}
        onClose={() => setActive(null)}
        onUpdate={reload}
      />
    </>
  );
}
export function ExerciseRunner({
  assignment,
  onClose,
  onUpdate,
}: {
  assignment: Assignment | null;
  onClose: () => void;
  onUpdate: () => void;
}) {
  const [current, setCurrent] = useState<Assignment | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    setCurrent(assignment);
    setText("");
  }, [assignment]);
  async function submit(answer: string) {
    if (!current) return;
    setBusy(true);
    try {
      const updated = await api<Partial<Assignment>>(
        `/exercises/${current.id}/answer`,
        "POST",
        { answer, expected_step: current.answers.length },
      );
      let next = { ...current, ...updated };
      if (next.answers.length === next.exercise.steps.length) {
        const done = await api<Partial<Assignment>>(
          `/exercises/${current.id}/complete`,
          "POST",
        );
        next = { ...next, ...done };
        toast.success("Упражнение выполнено. Результат сохранён.");
      }
      setCurrent(next);
      setText("");
      onUpdate();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      open={!!assignment}
      onOpenChange={(v) => {
        if (!v) onClose();
      }}
      title={current?.exercise.name || "Упражнение"}
    >
      {current &&
        (current.status === "completed" ? (
          <div className="form-stack">
            <div className="success-panel">
              <Check size={28} />
              <h3>Вы уделили время себе</h3>
              <p>Ответы сохранены в истории упражнения.</p>
            </div>
            {current.answers.map((a, i) => (
              <div className="answer-review" key={i}>
                <small>{current.exercise.steps[i]}</small>
                <p>{a}</p>
              </div>
            ))}
            <Button onClick={onClose}>Готово</Button>
          </div>
        ) : !current.available ? (
          <Empty
            title="Упражнение недоступно"
            text="Проверьте согласие и план сопровождения."
          />
        ) : current.answers.length === current.exercise.steps.length ? (
          <Button
            onClick={async () => {
              try {
                const result = await api<Partial<Assignment>>(
                  `/exercises/${current.id}/complete`,
                  "POST",
                );
                setCurrent({ ...current, ...result });
                onUpdate();
              } catch (e) {
                toast.error((e as Error).message);
              }
            }}
          >
            Завершить упражнение
          </Button>
        ) : current.exercise.type === "breathing" ? (
          <Breathing
            busy={busy}
            onComplete={() => submit("Практика спокойного дыхания завершена")}
          />
        ) : (
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              submit(text);
            }}
          >
            <div className="step-progress">
              {current.exercise.steps.map((_, i) => (
                <span
                  key={i}
                  className={i <= current.answers.length ? "filled" : ""}
                />
              ))}
            </div>
            <small className="muted">
              Шаг {current.answers.length + 1} из{" "}
              {current.exercise.steps.length}
            </small>
            <h3>{current.exercise.steps[current.answers.length]}</h3>
            <textarea
              autoFocus
              disabled={busy}
              required
              maxLength={4000}
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Можно ответить своими словами…"
            />
            <p className="muted">
              Отвечайте в своём темпе. Каждый шаг сохраняется отдельно.
            </p>
            <Button disabled={busy || !text.trim()}>
              {busy
                ? "Сохраняем…"
                : current.answers.length === current.exercise.steps.length - 1
                  ? "Завершить упражнение"
                  : "Следующий шаг"}
              <ArrowRight size={16} />
            </Button>
          </form>
        ))}
    </Modal>
  );
}
function Breathing({
  busy,
  onComplete,
}: {
  busy: boolean;
  onComplete: () => void;
}) {
  const [seconds, setSeconds] = useState(0);
  const [running, setRunning] = useState(false);
  const [duration, setDuration] = useState(120);
  useEffect(() => {
    if (!running || seconds >= duration) return;
    const timer = setInterval(
      () => setSeconds((s) => Math.min(s + 1, duration)),
      1000,
    );
    return () => clearInterval(timer);
  }, [running, seconds, duration]);
  const inhale = seconds % 8 < 4;
  return (
    <div className="breathing">
      <p>Дышите мягко, без задержек и усилий. При дискомфорте остановитесь.</p>
      <label>
        Продолжительность
        <select
          value={duration}
          disabled={seconds > 0}
          onChange={(e) => setDuration(Number(e.target.value))}
        >
          <option value={120}>2 минуты</option>
          <option value={60}>1 минута</option>
        </select>
      </label>
      <div
        className={
          "breath-orb " +
          (running && inhale && seconds < duration ? "inhale" : "")
        }
      >
        <span>
          {seconds >= duration
            ? "Готово"
            : !running
              ? "В своём темпе"
              : inhale
                ? "Вдох"
                : "Выдох"}
        </span>
      </div>
      <p>
        {Math.floor((duration - seconds) / 60)}:
        {String((duration - seconds) % 60).padStart(2, "0")}
      </p>
      {seconds >= duration ? (
        <Button disabled={busy} onClick={onComplete}>
          Сохранить выполнение <Check size={16} />
        </Button>
      ) : (
        <Button variant="secondary" onClick={() => setRunning(!running)}>
          {running ? <Pause size={16} /> : <Play size={16} />}{" "}
          {running ? "Пауза" : seconds ? "Продолжить" : "Начать"}
        </Button>
      )}
    </div>
  );
}
export function Privacy() {
  const { data, setData, reload, error } = useData<Consent>("/consent");
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  async function update(values: Consent) {
    const previous = data;
    setData(values);
    setBusy(true);
    try {
      const saved = await api<Consent>("/consent", "PUT", values);
      setData(saved);
      toast.success("Разрешения обновлены");
    } catch (e) {
      setData(previous);
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow="ВАШИ ДАННЫЕ — ВАШ ВЫБОР"
        title="Приватность"
        subtitle="Вы управляете доступом психолога. Изменения действуют сразу."
      />
      {error ? (
        <p>{error}</p>
      ) : !data ? (
        <Loading />
      ) : (
        <section className="card privacy-card">
          <span className="soft-icon">
            <ShieldCheck />
          </span>
          <h2>Чем вы готовы поделиться?</h2>
          <p>
            Психолог не видит ваши переписки с ИИ. Для дневника, аналитики и
            результатов упражнений действуют отдельные разрешения.
          </p>
          {(
            [
              [
                "consent_status",
                "Сопровождение психологом",
                "Общее согласие. При отзыве весь доступ психолога закрывается.",
              ],
              [
                "share_journal",
                "Записи дневника",
                "Тексты, даты, настроение и теги.",
              ],
              [
                "share_analytics",
                "Эмоциональная динамика и AI-наблюдения",
                "Графики, отчёты и цитаты из записей, подтверждающие наблюдения.",
              ],
              [
                "share_exercises",
                "Результаты упражнений",
                "Назначения, прогресс и ваши ответы.",
              ],
            ] as const
          ).map(([key, title, desc]) => (
            <label className="privacy-toggle" key={key}>
              <span>
                <b>{title}</b>
                <small>{desc}</small>
              </span>
              <input
                type="checkbox"
                role="switch"
                checked={data[key]}
                disabled={
                  busy || (key !== "consent_status" && !data.consent_status)
                }
                onChange={(e) => update({ ...data, [key]: e.target.checked })}
              />
            </label>
          ))}
        </section>
      )}
      <section className="card privacy-card">
        <h2>Удаление данных</h2>
        <p>
          Удаляются профиль, переписки, дневник, результаты упражнений и отчёты.
          Действие нельзя отменить.
        </p>
        <Button variant="destructive" onClick={() => setConfirm(true)}>
          Удалить мой аккаунт и данные
        </Button>
      </section>
      <Modal
        open={confirm}
        onOpenChange={setConfirm}
        title="Удалить все ваши данные?"
      >
        <p>Это необратимо. После удаления вы выйдете из аккаунта.</p>
        <Button
          variant="destructive"
          onClick={async () => {
            try {
              await api("/me/data", "DELETE");
              location.href = "/login";
            } catch (e) {
              toast.error((e as Error).message);
            }
          }}
        >
          Да, удалить все данные
        </Button>
      </Modal>
    </>
  );
}
