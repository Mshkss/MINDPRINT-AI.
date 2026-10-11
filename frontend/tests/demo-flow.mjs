import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
const base = process.env.BASE_URL || "http://localhost:3000";
const browser = await chromium.launch({
  headless: true,
  ...(process.env.MINDPRINT_BROWSER
    ? { executablePath: process.env.MINDPRINT_BROWSER }
    : {}),
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
});
const page = await context.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const check = (value, message) => {
  if (!value) throw Error(message);
};
await mkdir("../docs/qa", { recursive: true });
try {
  // Restore only the known synthetic patient's consent before a repeat run.
  await context.request.post(base + "/api/auth/demo", {
    data: { role: "patient" },
  });
  await context.request.put(base + "/api/consent", {
    data: {
      consent_status: true,
      share_journal: true,
      share_analytics: true,
      share_exercises: true,
    },
  });
  await context.request.post(base + "/api/auth/logout");
  await page.goto(base);
  await page
    .getByRole("link", { name: "Попробовать демо", exact: true })
    .waitFor();
  await page.screenshot({
    path: "../docs/qa/landing.png",
    fullPage: true,
    animations: "disabled",
  });
  await page
    .getByRole("link", { name: "Попробовать демо", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Войти как психолог", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Панель психолога", exact: true })
    .waitFor();
  await page
    .getByRole("link", { name: "Открыть", exact: false })
    .first()
    .click();
  await page.getByRole("heading", { name: "Александр", exact: true }).waitFor();
  await page.getByText("Эмоциональная динамика", { exact: true }).waitFor();
  const pid = Number(new URL(page.url()).pathname.split("/").at(-1));
  await page.screenshot({
    path: "../docs/qa/psychologist.png",
    fullPage: true,
    animations: "disabled",
  });
  await page
    .getByRole("button", { name: "Назначить упражнение", exact: true })
    .click();
  const assignmentDialog = page.getByRole("dialog");
  await assignmentDialog
    .locator(".assign-choice")
    .filter({ hasText: "Дневник мыслей" })
    .getByRole("button", { name: "Назначить", exact: true })
    .click();
  await assignmentDialog.waitFor({ state: "hidden" });
  await page
    .getByRole("button", { name: "Кабинет пациента", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Привет, Александр", exact: true })
    .waitFor();
  await page.getByRole("button", { name: "Хорошо", exact: true }).click();
  await page.getByText("Настроение сохранено", { exact: true }).waitFor();
  await page.screenshot({
    path: "../docs/qa/patient.png",
    fullPage: true,
    animations: "disabled",
  });
  await page
    .getByRole("link", { name: "Начать разговор", exact: true })
    .click();
  await page
    .getByRole("button", { name: /Попробовать демонстрационный сценарий/ })
    .click();
  await page
    .locator(".message.assistant")
    .filter({ hasText: "Дневник мыслей" })
    .waitFor();
  await page.screenshot({
    path: "../docs/qa/chat.png",
    fullPage: true,
    animations: "disabled",
  });
  await page
    .locator(".chat-assignments")
    .getByRole("button", { name: /Дневник мыслей/ })
    .click();
  const dialog = page.getByRole("dialog");
  const answers = [
    "Начальник попросил переделать отчёт.",
    "Кажется, что меня хотят уволить.",
    "Тревога и страх оценки.",
    "За: попросил доработать. Против: об увольнении никто не говорил.",
    "Это обычная обратная связь по задаче, я могу уточнить ожидания.",
  ];
  const stepLabel = await dialog
    .locator("small")
    .filter({ hasText: /Шаг [0-9]+ из/ })
    .innerText();
  const start = Number(stepLabel.match(/Шаг ([0-9]+)/)[1]) - 1;
  for (let i = start; i < answers.length; i++) {
    await dialog.getByText(`Шаг ${i + 1} из 5`, { exact: true }).waitFor();
    await dialog.locator("textarea").fill(answers[i]);
    await dialog
      .getByRole("button", {
        name: i === 4 ? "Завершить упражнение" : "Следующий шаг",
        exact: true,
      })
      .click();
  }
  await dialog
    .getByRole("heading", { name: "Вы уделили время себе", exact: true })
    .waitFor();
  await dialog.getByRole("button", { name: "Готово", exact: true }).click();
  await page
    .getByRole("button", { name: "Кабинет психолога", exact: true })
    .click();
  await page
    .getByRole("link", { name: "Открыть", exact: false })
    .first()
    .click();
  await page.getByRole("button", { name: "Упражнения", exact: true }).click();
  await page
    .locator(".exercise-row")
    .filter({ hasText: "Дневник мыслей" })
    .first()
    .click();
  await page
    .getByRole("dialog")
    .getByText(answers[4], { exact: true })
    .waitFor();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Закрыть", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Сформировать отчёт", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("heading", { name: "Аналитический отчёт", exact: true })
    .waitFor();
  await page
    .getByRole("heading", { name: "Источники и выводы", exact: true })
    .waitFor();
  check(
    (await page.locator(".report-source").count()) > 0,
    "Report has no evidence",
  );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Подтверждаю", exact: true })
    .first()
    .click();
  await page.getByText("Обратная связь сохранена", { exact: true }).waitFor();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Закрыть", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Кабинет пациента", exact: true })
    .click();
  await page.getByRole("link", { name: "Дневник", exact: true }).click();
  await page.getByRole("button", { name: "Новая запись", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByLabel("Ваши мысли", { exact: true })
    .fill("Тестовая синтетическая запись: стало спокойнее после упражнения.");
  await page
    .getByRole("button", { name: "Сохранить запись", exact: true })
    .click();
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  await page
    .getByText(
      "Тестовая синтетическая запись: стало спокойнее после упражнения.",
      { exact: true },
    )
    .first()
    .waitFor();
  await page.getByRole("link", { name: "Приватность", exact: true }).click();
  const general = page.getByRole("switch").first();
  await general.uncheck();
  await page.getByText("Разрешения обновлены", { exact: true }).waitFor();
  await page
    .getByRole("button", { name: "Кабинет психолога", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Панель психолога", exact: true })
    .waitFor();
  await page.locator("tbody").waitFor();
  check(
    (await page
      .locator("tbody")
      .getByText("Александр", { exact: true })
      .count()) === 0,
    "Revoked patient is still visible",
  );
  const forbidden = await page.request.get(`${base}/api/analytics/${pid}`);
  check(forbidden.status() === 403, "Revoked analytics accessible");
  await page
    .getByRole("button", { name: "Кабинет пациента", exact: true })
    .click();
  await page.getByRole("link", { name: "Приватность", exact: true }).click();
  await page.getByRole("switch").first().check();
  await page.getByText("Разрешения обновлены", { exact: true }).waitFor();
  await page
    .getByRole("link", { name: "Моё пространство", exact: true })
    .click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../docs/qa/mobile.png",
    fullPage: true,
    animations: "disabled",
  });
  check(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    "Mobile horizontal overflow",
  );
  await page.getByRole("button", { name: "Открыть меню" }).click();
  await page.getByRole("link", { name: "ИИ-компаньон", exact: true }).click();
  await page.locator(".chat-composer").waitFor();
  check(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    "Mobile chat overflow",
  );
  check(!errors.length, "Browser errors: " + errors.join("; "));
  console.log(
    "PASS: landing, demo login, assignment, context-aware chat, five saved steps, psychologist results, report evidence, feedback, journal, consent revocation/restoration, mobile layout.",
  );
} finally {
  await browser.close();
}
