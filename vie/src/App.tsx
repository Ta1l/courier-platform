import { useState } from "react";
import { Helmet } from "react-helmet-async";
import { useParams } from "react-router-dom";
import { getBotLink, getBotLinkCard } from "./config";
import { CTAButton } from "./components/common/CTAButton";
import { FAQItem } from "./components/common/FAQItem";
import { Icons } from "./components/common/Icons";
import { Section } from "./components/common/Section";
import { CalculatorModal } from "./components/modals/CalculatorModal";
import { EbikeModal } from "./components/modals/EbikeModal";
import { COPY } from "./content/copy";

export function App() {
  const { id } = useParams<{ id?: string }>();
  const campIdFromPath = id && /^\d+$/.test(id) ? id : undefined;
  const [ebikeModal, setEbikeModal] = useState(false);
  const [calcModal, setCalcModal] = useState(false);
  const [caseTab, setCaseTab] = useState<"case" | "table" | "calc">("case");
  /* CHANGE 2: dismissible banner state */
  const [bannerVisible, setBannerVisible] = useState(true);

  const botLink = getBotLink(undefined, campIdFromPath);
  const botLinkCard = getBotLinkCard(campIdFromPath);
  const canonicalUrl = campIdFromPath
    ? `https://kurer-spb.ru/camp/${campIdFromPath}`
    : "https://kurer-spb.ru/";
  const year = new Date().getFullYear();

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <Helmet>
        <link rel="canonical" href={canonicalUrl} />
        <meta name="robots" content="index, follow" />
        <meta property="og:url" content={canonicalUrl} />
      </Helmet>

      {/* ═══ CHANGE 2: FIXED TOP BONUS BANNER — dismissible, mobile-safe ═══
          CSS: .bonus-banner in index.css
          Responsive: compact on 360/375/412px, safe-area-inset for iOS
          To change banner height offsets: edit .header-with-banner and .hero-with-banner in CSS */}
      <div
        className={`bonus-banner bg-gradient-to-r from-amber-500 via-amber-400 to-amber-500 ${
          bannerVisible ? "" : "banner-hidden"
        }`}
        role="banner"
        aria-label={COPY.banner.ariaLabel}
      >
        <div className="bonus-shimmer absolute inset-0 pointer-events-none" />
        <a
          href={botLink}
          target="_blank"
          rel="noopener noreferrer"
          className="bonus-banner-inner relative font-bold text-amber-900"
        >
          <span>{COPY.banner.bonus}</span>
          <span className="hidden sm:inline">{COPY.banner.details}</span>
        </a>
        {/* CHANGE 2: close/dismiss button */}
        <button
          className="bonus-banner-close text-amber-900"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setBannerVisible(false);
          }}
          aria-label={COPY.banner.closeAriaLabel}
        >
          &times;
        </button>
      </div>

      {/* ─── HEADER / NAV ─── */}
      {/* CHANGE 2: header offset shifts when banner visible */}
      <header
        className={`sticky z-40 border-b border-[var(--color-border)] bg-white/90 backdrop-blur-md ${
          bannerVisible ? "header-with-banner" : "top-0"
        }`}
      >
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-2.5 sm:py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-brand)] text-white">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </div>
            <span className="text-sm font-bold sm:text-base">Курьеры СПб</span>
          </div>
          <a
            href={botLink}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--color-brand)] px-3.5 py-2 text-sm font-semibold text-white transition-colors hover:bg-[var(--color-brand-dark)] active:scale-[0.97] sm:px-4"
          >
            {Icons.telegram}
            <span className="hidden sm:inline">Пройти тест</span>
            <span className="sm:hidden">Тест</span>
          </a>
        </div>
      </header>

      {/* ═══ HERO ═══ */}
      {/* CHANGE 2: extra top padding when banner is visible */}
      <div className={`relative overflow-hidden bg-gradient-to-br from-[var(--color-brand-light)] via-white to-white ${bannerVisible ? "hero-with-banner" : ""}`}>
        <div className="absolute -right-20 -top-20 h-80 w-80 rounded-full bg-[var(--color-brand)]/5 blur-3xl" />
        <div className="absolute -left-20 bottom-0 h-60 w-60 rounded-full bg-[var(--color-brand)]/5 blur-3xl" />

        <div className="relative mx-auto max-w-6xl px-4 pb-10 pt-7 sm:pb-24 sm:pt-16">
          <div className="grid gap-8 lg:grid-cols-2 lg:items-center lg:gap-16">
            {/* Left Column */}
            <div className="animate-fade-in-up">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-[var(--color-brand)]/10 px-3.5 py-1.5 text-sm font-semibold text-[var(--color-brand)] sm:mb-4 sm:px-4">
                <span className="h-2 w-2 rounded-full bg-[var(--color-brand)] animate-pulse" />
                Набор открыт — Санкт-Петербург
              </div>
              <h1 className="mb-4 text-[1.75rem] font-extrabold leading-tight tracking-tight sm:mb-5 sm:text-4xl lg:text-[3.2rem]">
                Работа курьером в&nbsp;Санкт-Петербурге —{" "}
                <span className="text-[var(--color-brand)]">
                  от&nbsp;550&nbsp;₽/час
                </span>
              </h1>
              <p className="mb-6 max-w-lg text-base text-[var(--color-text-secondary)] sm:mb-8 sm:text-lg">
                Гибкий график, выплаты раз в&nbsp;неделю. Чтобы отправить
                заявку&nbsp;— пройдите быстрый тест в&nbsp;нашем Telegram-боте.
              </p>
              <CTAButton />
              <p className="mt-3 text-xs text-[var(--color-text-secondary)]">
                Требуется самозанятость. Возраст 16+
              </p>
            </div>

            {/* Right Column — Income Card */}
            <div className="animate-fade-in-up animate-delay-200">
              <div className="rounded-2xl border border-[var(--color-border)] bg-white p-5 shadow-xl shadow-black/5 sm:p-8">
                <h2 className="mb-5 text-center text-base font-bold sm:mb-6 sm:text-lg">
                  Коротко о доходе
                </h2>

                {/* CHANGE 1: "От 550 ₽/час" — single line, nowrap + clamp() */}
                <div className="mb-5 rounded-xl bg-[var(--color-brand)]/10 p-4 text-center sm:mb-6 sm:p-5">
                  <p className="rate-nowrap font-extrabold text-[var(--color-brand)]">
                    От 550&nbsp;₽/час
                  </p>
                  {/* CHANGE 1: working hours range */}
                  <p className="mt-1.5 text-xs text-[var(--color-text-secondary)] sm:text-sm">
                    Рабочий день: 4–16 часов
                  </p>
                  <p className="mt-0.5 text-[10px] text-[var(--color-text-secondary)] sm:text-xs">
                    чаевые и бонусы не учтены
                  </p>
                </div>

                {/* Three Stats */}
                <div className="grid grid-cols-3 gap-2 text-center sm:gap-3">
                  <div className="rounded-xl bg-[var(--color-bg-alt)] p-2.5 sm:p-3">
                    <p className="text-lg font-extrabold text-[var(--color-text)] sm:text-2xl">
                      2&nbsp;200&nbsp;₽
                    </p>
                    <p className="mt-0.5 text-[10px] text-[var(--color-text-secondary)] sm:mt-1 sm:text-xs">
                      за 4-ч смену
                    </p>
                  </div>
                  <div className="rounded-xl bg-[var(--color-bg-alt)] p-2.5 sm:p-3">
                    <p className="text-lg font-extrabold text-[var(--color-text)] sm:text-2xl">
                      4–16
                    </p>
                    <p className="mt-0.5 text-[10px] text-[var(--color-text-secondary)] sm:mt-1 sm:text-xs">
                      часов в день
                    </p>
                  </div>
                  <div className="rounded-xl bg-[var(--color-bg-alt)] p-2.5 sm:p-3">
                    <p className="text-lg font-extrabold text-[var(--color-text)] sm:text-2xl">
                      1×
                    </p>
                    <p className="mt-0.5 text-[10px] text-[var(--color-text-secondary)] sm:mt-1 sm:text-xs">
                      выплата в нед.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ═══ BONUS BLOCK — full-width, under Hero ═══ */}
      <Section className="bg-gradient-to-r from-amber-50 via-amber-100/80 to-amber-50 py-8 sm:py-12" id="bonus">
        <div className="mx-auto max-w-6xl px-4">
          <div className="rounded-2xl border-2 border-amber-300 bg-white p-5 text-center shadow-lg shadow-amber-100 sm:p-8">
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-100 text-amber-600 sm:h-16 sm:w-16">
              {Icons.gift}
            </div>
            <h2 className="mb-2 text-xl font-extrabold text-amber-800 sm:text-3xl">
              🎁 Стартовый бонус 10&nbsp;000–15&nbsp;000&nbsp;₽
            </h2>
            <p className="mx-auto max-w-md text-sm text-amber-700 sm:text-base">
              Дополнительный доход за&nbsp;выполнение условий&nbsp;— менеджер сообщит детали
            </p>
            <div className="mt-5">
              <CTAButton text="Узнать условия бонуса" />
            </div>
          </div>
        </div>
      </Section>

      {/* ═══ EARNINGS TABLE ═══ */}
      <Section className="bg-[var(--color-bg-alt)] py-12 sm:py-24" id="earnings">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="mb-3 text-center text-xl font-extrabold sm:text-3xl">
            Сколько можно заработать
          </h2>
          <p className="mx-auto mb-8 max-w-xl text-center text-sm text-[var(--color-text-secondary)] sm:mb-10 sm:text-base">
            Расчёт по ставке 550&nbsp;₽/час при работе 6&nbsp;дней
            в&nbsp;неделю. Бонусы и&nbsp;чаевые не учтены.
          </p>

          <div className="overflow-x-auto rounded-2xl border border-[var(--color-border)] bg-white shadow-sm">
            <table className="w-full text-left text-sm sm:text-base">
              <thead>
                <tr className="border-b border-[var(--color-border)] bg-[var(--color-bg-alt)]">
                  <th className="px-3 py-3 text-xs font-semibold sm:px-6 sm:text-sm">Часы/день</th>
                  <th className="px-3 py-3 text-xs font-semibold sm:px-6 sm:text-sm">В день</th>
                  <th className="px-3 py-3 text-xs font-semibold sm:px-6 sm:text-sm">В неделю</th>
                  <th className="px-3 py-3 text-xs font-semibold sm:px-6 sm:text-sm">В месяц</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { h: "4 ч",  d: "2 200 ₽",  w: "≈ 13 200 ₽",   m: "≈ 52 800 ₽" },
                  { h: "6 ч",  d: "3 300 ₽",  w: "≈ 19 800 ₽",   m: "≈ 79 200 ₽" },
                  { h: "8 ч",  d: "4 400 ₽",  w: "≈ 26 400 ₽",   m: "≈ 105 600 ₽", highlight: true },
                  { h: "10 ч", d: "5 500 ₽",  w: "≈ 33 000 ₽",   m: "≈ 132 000 ₽" },
                  { h: "14 ч", d: "7 700 ₽",  w: "≈ 46 200 ₽",   m: "≈ 184 800 ₽" },
                  { h: "16 ч", d: "8 800 ₽",  w: "≈ 52 800 ₽",   m: "≈ 211 200 ₽" },
                ].map((r, i) => (
                  <tr
                    key={i}
                    className={`border-b border-[var(--color-border)] last:border-0 ${r.highlight ? "bg-[var(--color-brand)]/5 font-semibold" : ""}`}
                  >
                    <td className="px-3 py-3 text-xs sm:px-6 sm:text-base">{r.h}</td>
                    <td className="px-3 py-3 text-xs sm:px-6 sm:text-base">{r.d}</td>
                    <td className="px-3 py-3 text-xs sm:px-6 sm:text-base">{r.w}</td>
                    <td className="px-3 py-3 text-xs font-bold text-[var(--color-brand)] sm:px-6 sm:text-base">
                      {r.m}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* "Реальный пример" — 3 tabs */}
          <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-white sm:mt-8">
            <div className="flex border-b border-[var(--color-border)] overflow-x-auto">
              {[
                { key: "case" as const,  label: "Кейс",        icon: Icons.user },
                { key: "table" as const, label: "Таблица",     icon: Icons.table },
                { key: "calc" as const,  label: "Калькулятор", icon: Icons.calculator },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => {
                    if (tab.key === "calc") {
                      setCalcModal(true);
                    } else {
                      setCaseTab(tab.key);
                    }
                  }}
                  className={`flex items-center gap-1.5 px-4 py-3 text-xs font-semibold transition-colors sm:px-6 sm:text-sm ${
                    caseTab === tab.key && tab.key !== "calc"
                      ? "tab-active text-[var(--color-brand)]"
                      : "text-[var(--color-text-secondary)] hover:text-[var(--color-brand)]"
                  }`}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Tab: Case card (default) */}
            {caseTab === "case" && (
              <div className="p-5 sm:p-8">
                <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[var(--color-brand)]/10 text-[var(--color-brand)]">
                    {Icons.ruble}
                  </div>
                  <div className="flex-1">
                    <p className="mb-3 text-sm font-bold text-[var(--color-brand)]">
                      Реальный пример: путь нового курьера
                    </p>
                    <div className="mb-4 grid grid-cols-3 gap-2">
                      <div className="rounded-xl bg-[var(--color-bg-alt)] p-3 text-center">
                        <p className="text-lg font-extrabold sm:text-2xl">СПб</p>
                        <p className="text-[10px] text-[var(--color-text-secondary)] sm:text-xs">город</p>
                      </div>
                      <div className="rounded-xl bg-[var(--color-bg-alt)] p-3 text-center">
                        <p className="text-lg font-extrabold sm:text-2xl">8 ч</p>
                        <p className="text-[10px] text-[var(--color-text-secondary)] sm:text-xs">смена</p>
                      </div>
                      <div className="rounded-xl bg-[var(--color-brand)]/10 p-3 text-center">
                        <p className="text-lg font-extrabold text-[var(--color-brand)] sm:text-2xl">100K+</p>
                        <p className="text-[10px] text-[var(--color-text-secondary)] sm:text-xs">₽/мес</p>
                      </div>
                    </div>
                    <p className="text-sm text-[var(--color-text)] sm:text-base">
                      Курьер подключился к&nbsp;сервису без опыта. В&nbsp;первый месяц работал по&nbsp;6&nbsp;часов,
                      5&nbsp;дней в&nbsp;неделю и&nbsp;заработал <strong>≈&nbsp;66&nbsp;000&nbsp;₽</strong>.
                      Со&nbsp;второго месяца увеличил смены до&nbsp;8&nbsp;часов, взял электровелосипед в&nbsp;аренду
                      (менеджер помог подобрать вариант) и&nbsp;стабильно выходит
                      на&nbsp;<strong>100&nbsp;000+&nbsp;₽/мес</strong>.
                    </p>
                    <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3">
                      <p className="text-xs font-semibold text-amber-700 sm:text-sm">
                        🎁 + Стартовый бонус 10&nbsp;000–15&nbsp;000&nbsp;₽ за&nbsp;выполнение условий
                      </p>
                    </div>
                    <p className="mt-3 text-xs text-[var(--color-text-secondary)]">
                      Без учёта чаевых и дополнительных выплат
                    </p>
                  </div>
                </div>

                <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                  <CTAButton text="Начать так же" className="flex-1" />
                  <button
                    onClick={() => setCalcModal(true)}
                    className="inline-flex items-center justify-center gap-2 rounded-xl border-2 border-[var(--color-brand)] px-5 py-3 text-sm font-semibold text-[var(--color-brand)] transition-all hover:bg-[var(--color-brand-light)] active:scale-[0.97] sm:px-6"
                  >
                    {Icons.calculator}
                    Посчитать свой доход
                  </button>
                </div>
              </div>
            )}

            {/* Tab: Table */}
            {caseTab === "table" && (
              <div className="p-5 sm:p-8">
                <p className="mb-4 text-sm font-bold text-[var(--color-text)]">
                  Прогресс нового курьера (СПб, 5 дней/нед)
                </p>
                <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-[var(--color-border)] bg-[var(--color-bg-alt)]">
                        <th className="px-3 py-2.5 text-xs font-semibold sm:px-5 sm:text-sm">Период</th>
                        <th className="px-3 py-2.5 text-xs font-semibold sm:px-5 sm:text-sm">Часы/день</th>
                        <th className="px-3 py-2.5 text-xs font-semibold sm:px-5 sm:text-sm">Дни/нед</th>
                        <th className="px-3 py-2.5 text-xs font-semibold sm:px-5 sm:text-sm">Доход</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-[var(--color-border)]">
                        <td className="px-3 py-2.5 text-xs sm:px-5 sm:text-sm">1-й месяц</td>
                        <td className="px-3 py-2.5 text-xs sm:px-5 sm:text-sm">6</td>
                        <td className="px-3 py-2.5 text-xs sm:px-5 sm:text-sm">5</td>
                        <td className="px-3 py-2.5 text-xs font-bold text-[var(--color-brand)] sm:px-5 sm:text-sm">≈ 66 000 ₽</td>
                      </tr>
                      <tr className="border-b border-[var(--color-border)] bg-[var(--color-brand)]/5">
                        <td className="px-3 py-2.5 text-xs font-medium sm:px-5 sm:text-sm">2-й месяц</td>
                        <td className="px-3 py-2.5 text-xs sm:px-5 sm:text-sm">8</td>
                        <td className="px-3 py-2.5 text-xs sm:px-5 sm:text-sm">5</td>
                        <td className="px-3 py-2.5 text-xs font-bold text-[var(--color-brand)] sm:px-5 sm:text-sm">≈ 88 000 ₽</td>
                      </tr>
                      <tr className="border-b border-[var(--color-border)] bg-amber-50">
                        <td className="px-3 py-2.5 text-xs font-medium text-amber-700 sm:px-5 sm:text-sm">+ бонус</td>
                        <td className="px-3 py-2.5 text-xs text-[var(--color-text-secondary)] sm:px-5 sm:text-sm">—</td>
                        <td className="px-3 py-2.5 text-xs text-[var(--color-text-secondary)] sm:px-5 sm:text-sm">—</td>
                        <td className="px-3 py-2.5 text-xs font-bold text-amber-700 sm:px-5 sm:text-sm">+10 000–15 000 ₽</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p className="mt-3 text-[11px] text-[var(--color-text-secondary)]">
                  Без учёта чаевых и дополнительных выплат
                </p>
                <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                  <CTAButton text="Начать зарабатывать" className="flex-1" />
                  <button
                    onClick={() => setCalcModal(true)}
                    className="inline-flex items-center justify-center gap-2 rounded-xl border-2 border-[var(--color-brand)] px-5 py-3 text-sm font-semibold text-[var(--color-brand)] transition-all hover:bg-[var(--color-brand-light)] active:scale-[0.97] sm:px-6"
                  >
                    {Icons.calculator}
                    Посчитать свой доход
                  </button>
                </div>
              </div>
            )}
          </div>

          <p className="mt-4 text-center text-[11px] text-[var(--color-text-secondary)] sm:text-xs">
            * Чаевые и бонусы не учтены в расчётах. Фактический доход может отличаться.
          </p>
        </div>
      </Section>

      {/* ─── ADVANTAGES ─── */}
      <Section className="py-12 sm:py-24" id="advantages">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="mb-3 text-center text-xl font-extrabold sm:text-3xl">
            Почему это выгодно
          </h2>
          <p className="mx-auto mb-8 max-w-lg text-center text-sm text-[var(--color-text-secondary)] sm:mb-10 sm:text-base">
            Простые условия и прозрачный заработок
          </p>
          <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-5">
            {/* CHANGE 1b: added 5th advantage — delivery services */}
            {[
              { icon: Icons.clock,     title: "Гибкий график",        desc: "Работайте 4–16 ч в день, подбирайте смены под себя" },
              { icon: Icons.wallet,    title: "Выплаты раз в неделю", desc: "Стабильные еженедельные выплаты на карту" },
              { icon: Icons.rocket,    title: "Старт без опыта",      desc: "Менеджер поможет разобраться и выйти на первую смену" },
              { icon: Icons.shield,    title: "Самозанятость",        desc: "Оформление через статус самозанятого — быстро и просто" },
              /* CHANGE 1b: новая карточка — сервисы доставки */
              { icon: Icons.building,  title: "Крупные сервисы",      desc: "Яндекс, Магнит, Самокат — менеджер поможет с выбором" },
            ].map((item, i) => (
              <div
                key={i}
                className={`group rounded-2xl border border-[var(--color-border)] bg-white p-4 transition-all duration-200 hover:border-[var(--color-brand)]/30 hover:shadow-lg hover:shadow-[var(--color-brand)]/5 sm:p-6 ${i === 4 ? "col-span-2 lg:col-span-1" : ""}`}
              >
                <div className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--color-brand)]/10 text-[var(--color-brand)] transition-colors group-hover:bg-[var(--color-brand)] group-hover:text-white sm:mb-4 sm:h-14 sm:w-14">
                  {item.icon}
                </div>
                <h3 className="mb-1 text-sm font-bold sm:mb-2 sm:text-base">{item.title}</h3>
                <p className="text-xs text-[var(--color-text-secondary)] sm:text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* ─── WHO CAN WORK ─── */}
      <Section className="bg-[var(--color-bg-alt)] py-12 sm:py-24" id="requirements">
        <div className="mx-auto max-w-6xl px-4">
          <div className="grid gap-8 lg:grid-cols-2 lg:items-center lg:gap-10">
            <div>
              <h2 className="mb-3 text-xl font-extrabold sm:text-3xl">
                Кто может работать
              </h2>
              <p className="mb-5 text-sm text-[var(--color-text-secondary)] sm:mb-6 sm:text-base">
                Принимаем граждан РФ и&nbsp;стран ЕАЭС. Возраст&nbsp;— от&nbsp;16&nbsp;лет.
              </p>

              <div className="space-y-2 sm:space-y-3">
                {[
                  { flag: "🇷🇺", country: "Россия", note: "" },
                  { flag: "🇧🇾", country: "Беларусь", note: "ЕАЭС" },
                  { flag: "🇰🇿", country: "Казахстан", note: "ЕАЭС" },
                  { flag: "🇦🇲", country: "Армения", note: "ЕАЭС" },
                  { flag: "🇰🇬", country: "Киргизия", note: "ЕАЭС" },
                ].map((c, i) => (
                  <div key={i} className="flex items-center gap-3 rounded-xl bg-white px-3.5 py-2.5 shadow-sm sm:px-4 sm:py-3">
                    <span className="text-xl sm:text-2xl">{c.flag}</span>
                    <span className="text-sm font-medium sm:text-base">{c.country}</span>
                    {c.note && (
                      <span className="ml-auto rounded-full bg-[var(--color-brand)]/10 px-2 py-0.5 text-[10px] font-semibold text-[var(--color-brand)] sm:px-2.5 sm:text-xs">
                        {c.note}
                      </span>
                    )}
                    <span className="text-[var(--color-brand)]">{Icons.check}</span>
                  </div>
                ))}
              </div>

              <p className="mt-4 text-xs text-[var(--color-text-secondary)]">
                Граждане других стран (не&nbsp;ЕАЭС) не&nbsp;могут быть приняты на&nbsp;работу.
              </p>
            </div>

            <div className="rounded-2xl border border-[var(--color-border)] bg-white p-5 sm:p-8">
              <h3 className="mb-4 text-base font-bold sm:text-lg">Возрастные требования</h3>
              <div className="space-y-3 sm:space-y-4">
                <div className="rounded-xl bg-[var(--color-brand)]/5 p-3.5 sm:p-4">
                  <p className="font-semibold text-[var(--color-brand)]">18+ лет</p>
                  <p className="text-xs text-[var(--color-text-secondary)] sm:text-sm">
                    Полный рабочий день без ограничений — до 16 ч/день
                  </p>
                </div>
                <div className="rounded-xl bg-amber-50 p-3.5 sm:p-4">
                  <p className="font-semibold text-amber-700">16–17 лет</p>
                  <p className="text-xs text-[var(--color-text-secondary)] sm:text-sm">
                    Сокращённое рабочее время: до 7 ч/день. При совмещении с&nbsp;учёбой — до 4 ч/день.
                  </p>
                  <a
                    href="#footer-legal"
                    className="mt-2 inline-block text-xs font-medium text-amber-700 underline hover:no-underline"
                  >
                    Подробнее о правилах для 16–18 лет →
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* ─── STEPS ─── */}
      <Section className="py-12 sm:py-24" id="steps">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="mb-3 text-center text-xl font-extrabold sm:text-3xl">
            Как подключиться
          </h2>
          <p className="mx-auto mb-8 max-w-lg text-center text-sm text-[var(--color-text-secondary)] sm:mb-12 sm:text-base">
            Три простых шага — от заявки до первой смены
          </p>

          <div className="grid gap-6 sm:grid-cols-3 sm:gap-8">
            {[
              {
                icon: Icons.steps1, step: "1",
                title: "Пройдите тест в боте",
                desc: "Ответьте на несколько вопросов в Telegram-боте — это занимает 2–3 минуты. Анкета сразу попадает к менеджеру.",
              },
              {
                icon: Icons.steps2, step: "2",
                title: "Менеджер свяжется с вами",
                /* CHANGE 1a: добавлен текст про сервисы доставки в шаге 2 */
                desc: "Мы проверим данные, поможем с оформлением самозанятости, арендой оборудования и электровелосипеда. Доставка через Яндекс, Магнит, Самокат — менеджер подберёт оптимальный сервис и маршрут.",
              },
              {
                icon: Icons.steps3, step: "3",
                title: "Выходите на смену",
                desc: "Получаете инструкцию, выбираете удобный график и начинаете зарабатывать.",
              },
            ].map((s, i) => (
              <div key={i} className="relative rounded-2xl border border-[var(--color-border)] bg-white p-5 text-center sm:p-6">
                <div className="absolute -top-4 left-1/2 flex h-8 w-8 -translate-x-1/2 items-center justify-center rounded-full bg-[var(--color-brand)] text-sm font-bold text-white">
                  {s.step}
                </div>
                <div className="mx-auto mb-3 mt-2 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-brand)]/10 text-[var(--color-brand)] sm:mb-4 sm:h-14 sm:w-14">
                  {s.icon}
                </div>
                <h3 className="mb-2 text-sm font-bold sm:text-base">{s.title}</h3>
                <p className="text-xs text-[var(--color-text-secondary)] sm:text-sm">{s.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 text-center sm:mt-10">
            <CTAButton />
            <p className="mt-3 text-xs text-[var(--color-text-secondary)]">
              Заполненная в боте анкета — готовая форма для работодателя
            </p>
          </div>
        </div>
      </Section>

      {/* ═══ CHANGE 3: E-BIKE SECTION — new icon, updated text ═══ */}
      <Section className="bg-[var(--color-bg-alt)] py-12 sm:py-24" id="ebike">
        <div className="mx-auto max-w-6xl px-4">
          <div className="grid gap-8 lg:grid-cols-2 lg:items-center lg:gap-10">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-[var(--color-brand)]/10 px-3.5 py-1.5 text-sm font-semibold text-[var(--color-brand)] sm:mb-4 sm:px-4">
                {/* CHANGE 3: icon reference — /assets/icons/bike-e.svg */}
                {Icons.bike}
                Бонус к заработку
              </div>
              <h2 className="mb-3 text-xl font-extrabold sm:mb-4 sm:text-3xl">
                Электровелосипед — ваш бонус к&nbsp;заработку
              </h2>

              {/* CHANGE 3: new large headline */}
              <p className="mb-4 text-lg font-bold text-[var(--color-brand)] sm:text-xl">
                ⚡ Быстрее доставка → больше заказов → выше заработок
              </p>

              {/* CHANGE 3: updated description */}
              <p className="mb-5 text-sm text-[var(--color-text-secondary)] sm:mb-6 sm:text-base">
                Электровелосипед повышает эффективность смены&nbsp;— менеджер
                поможет с&nbsp;арендой и&nbsp;подключением. Больше заказов за&nbsp;час,
                меньше утомления, выше выработка.
              </p>

              <div className="mb-5 grid grid-cols-3 gap-2 sm:mb-6 sm:gap-3">
                <div className="rounded-xl bg-white p-3 text-center shadow-sm sm:p-4">
                  <p className="text-xl font-extrabold text-[var(--color-brand)] sm:text-2xl">+30%</p>
                  <p className="text-[10px] text-[var(--color-text-secondary)] sm:text-xs">заказов за смену</p>
                </div>
                <div className="rounded-xl bg-white p-3 text-center shadow-sm sm:p-4">
                  <p className="text-xl font-extrabold text-[var(--color-brand)] sm:text-2xl">−50%</p>
                  <p className="text-[10px] text-[var(--color-text-secondary)] sm:text-xs">усталости</p>
                </div>
                <div className="rounded-xl bg-white p-3 text-center shadow-sm sm:p-4">
                  <p className="text-xl font-extrabold text-[var(--color-brand)] sm:text-2xl">↑</p>
                  <p className="text-[10px] text-[var(--color-text-secondary)] sm:text-xs">доход в час</p>
                </div>
              </div>

              <button
                onClick={() => setEbikeModal(true)}
                className="inline-flex items-center gap-2 rounded-xl border-2 border-[var(--color-brand)] px-5 py-3 text-sm font-semibold text-[var(--color-brand)] transition-all duration-200 hover:bg-[var(--color-brand-light)] active:scale-[0.97] sm:px-6 sm:py-3.5 sm:text-base"
              >
                Узнать про аренду электровелосипеда
              </button>
            </div>

            {/* CHANGE 3: updated illustration with new large e-bike SVG icon */}
            <div className="flex items-center justify-center">
              <div className="relative w-full max-w-sm">
                <div className="rounded-2xl bg-gradient-to-br from-[var(--color-brand)]/20 to-[var(--color-brand)]/5 p-6 text-center sm:p-8">
                  <div className="mx-auto mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-white text-[var(--color-brand)] shadow-lg sm:h-28 sm:w-28">
                    {/* CHANGE 3: large retina-crisp e-bike SVG — file ref: /assets/icons/bike-e.svg */}
                    {Icons.bikeLarge}
                  </div>
                  <h3 className="mb-2 text-lg font-bold sm:text-xl">Электровелосипед</h3>
                  <p className="text-sm font-semibold text-[var(--color-brand)]">
                    ⚡ Быстрее · Больше · Выше
                  </p>
                  <p className="mt-1 text-xs text-[var(--color-text-secondary)] sm:text-sm">
                    Менеджер поможет с арендой
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* ═══ "Проблемы с картой" — "готовое решение" ═══ */}
      <Section className="py-12 sm:py-24" id="card-help">
        <div className="mx-auto max-w-6xl px-4">
          <div className="rounded-2xl border border-[var(--color-border)] bg-gradient-to-r from-blue-50 to-indigo-50 p-5 sm:p-10">
            <div className="flex flex-col items-start gap-5 sm:flex-row sm:items-center sm:gap-6">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-blue-100 text-blue-600 sm:h-16 sm:w-16">
                {Icons.card}
              </div>
              <div className="flex-1">
                <h2 className="mb-2 text-lg font-extrabold sm:text-2xl">
                  Проблемы с картами? Поможем
                </h2>
                {/* "готовое решение" */}
                <p className="text-sm text-[var(--color-text-secondary)] sm:text-base">
                  У вас заблокированы карты или проблемы с&nbsp;платёжными
                  сервисами? Наш менеджер подскажет варианты&nbsp;— готовое
                  решение и&nbsp;рекомендации, чтобы вы&nbsp;могли начать
                  работать быстрее.
                </p>
              </div>
              <CTAButton
                text="Нужна помощь с картой"
                href={botLinkCard}
                secondary
                className="w-full shrink-0 sm:w-auto"
              />
            </div>
          </div>
        </div>
      </Section>

      {/* ─── FAQ ─── */}
      <Section className="bg-[var(--color-bg-alt)] py-12 sm:py-24" id="faq">
        <div className="mx-auto max-w-3xl px-4">
          <h2 className="mb-3 text-center text-xl font-extrabold sm:text-3xl">
            Частые вопросы
          </h2>
          <p className="mx-auto mb-8 max-w-lg text-center text-sm text-[var(--color-text-secondary)] sm:mb-10 sm:text-base">
            Ответы на самые частые вопросы о работе курьером
          </p>

          <div className="rounded-2xl border border-[var(--color-border)] bg-white p-4 sm:p-8">
            <FAQItem
              q="Нужна ли ИП для работы?"
              a="Нет, ИП не нужно. Требуется оформить статус самозанятого — это бесплатно и занимает несколько минут через приложение «Мой налог»."
            />
            <FAQItem
              q="Когда выплаты?"
              a="Выплаты производятся раз в неделю на вашу карту."
            />
            <FAQItem
              q="Что делать, если нет электровелосипеда?"
              a="Менеджер поможет с арендой электровелосипеда. Средняя стоимость — 5 500 ₽/неделя, при более длительной аренде действуют скидки."
            />
            {/* CHANGE 1c: FAQ — вопрос про сервисы доставки */}
            <FAQItem
              q="Через какие сервисы идёт доставка?"
              a="Доставка проходит через сервисы: Яндекс, Магнит, Самокат. Выбор сервиса и оптимальный маршрут подберёт менеджер при подключении."
            />
            <FAQItem
              q="Какие часы работы для 16–17 лет?"
              a={
                <>
                  Для несовершеннолетних 16–17 лет действуют сокращённые нормы:
                  до 7&nbsp;часов в&nbsp;день. При совмещении с&nbsp;учёбой — до
                  4&nbsp;часов в&nbsp;день.{" "}
                  <a
                    href="https://www.consultant.ru/document/cons_doc_LAW_34683/b09da1978a66a385bda15a2a0ad439257012a357/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[var(--color-brand)] underline hover:no-underline"
                  >
                    Подробнее (ТК РФ, ст. 94) →
                  </a>
                </>
              }
            />
            <FAQItem
              q="Могу ли я работать, если я гражданин другой страны (не ЕАЭС)?"
              a="К сожалению, нет. Мы принимаем только граждан РФ и стран ЕАЭС (Беларусь, Казахстан, Армения, Киргизия)."
            />
            <FAQItem
              q="Как быстро можно начать работать?"
              a="После прохождения теста в боте менеджер свяжется с вами, как правило, в течение 1 рабочего дня. Выход на первую смену — от 1 до 3 дней."
            />
          </div>
        </div>
      </Section>

      {/* ═══ FINAL CTA ═══ */}
      <Section className="py-12 sm:py-24">
        <div className="mx-auto max-w-6xl px-4 text-center">
          <div className="relative rounded-2xl bg-gradient-to-br from-[var(--color-brand)] to-[var(--color-brand-dark)] px-5 py-10 text-white sm:px-12 sm:py-16">
            {/* Bonus badge */}
            <div className="bonus-glow mx-auto mb-5 inline-flex items-center gap-2 rounded-full bg-amber-400/90 px-4 py-2 text-sm font-bold text-amber-900 sm:px-5 sm:text-base">
              🎁 Бонус 10&nbsp;000–15&nbsp;000&nbsp;₽
            </div>

            <h2
              className="mb-3 font-extrabold leading-tight tracking-tight sm:mb-4"
              style={{
                fontSize: "clamp(1.75rem, 4.5vw, 2.75rem)",
                WebkitFontSmoothing: "antialiased",
                textRendering: "optimizeLegibility",
              }}
            >
              Готовы начать зарабатывать от&nbsp;550&nbsp;₽/час?
            </h2>

            <p
              className="mx-auto mb-6 max-w-lg text-white/85 sm:mb-8"
              style={{ fontSize: "clamp(1rem, 2vw, 1.25rem)" }}
            >
              Пройдите быстрый тест в&nbsp;Telegram&nbsp;— это займёт
              2–3&nbsp;минуты. Менеджер свяжется с&nbsp;вами и&nbsp;поможет выйти
              на&nbsp;первую смену.
            </p>

            <a
              href={botLink}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-pulse inline-flex items-center justify-center gap-2.5 rounded-xl bg-white px-7 py-4 text-base font-bold text-[var(--color-brand)] shadow-lg shadow-black/10 transition-all duration-200 hover:bg-gray-50 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-[var(--color-brand)] active:scale-[0.97] sm:px-9 sm:py-5 sm:text-lg"
              style={{ borderRadius: "12px" }}
            >
              {Icons.telegram}
              Пройти тест
            </a>

            {/* CHANGE 1d: delivery services note under final CTA button */}
            <p className="mt-4 text-xs text-white/70 sm:text-sm">
              Доставка через Яндекс / Магнит / Самокат — менеджер подскажет лучший вариант
            </p>
            <p className="mt-1 text-xs text-white/50">
              Гибкий график · Выплаты раз в неделю · Чаевые и бонусы сверху
            </p>
          </div>
        </div>
      </Section>

      {/* ─── FOOTER ─── */}
      <footer
        id="footer-legal"
        className="border-t border-[var(--color-border)] bg-[var(--color-bg-alt)] py-8 sm:py-10"
      >
        <div className="mx-auto max-w-6xl px-4">
          <div className="grid gap-6 sm:grid-cols-2 sm:gap-8 lg:grid-cols-3">
            <div>
              <div className="mb-3 flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--color-brand)] text-white">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                  </svg>
                </div>
                <span className="text-sm font-bold">Сервис набора курьеров</span>
              </div>
              <p className="text-xs text-[var(--color-text-secondary)]">
                Санкт-Петербург. Связь с менеджером через Telegram-бот.
              </p>
            </div>

            <div>
              <p className="mb-2 text-sm font-semibold">Полезные ссылки</p>
              <ul className="space-y-1 text-xs text-[var(--color-text-secondary)]">
                <li>
                  <a
                    href="https://www.consultant.ru/document/cons_doc_LAW_34683/b09da1978a66a385bda15a2a0ad439257012a357/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-[var(--color-brand)] hover:underline"
                  >
                    ТК РФ, ст. 94 — продолжительность рабочего дня несовершеннолетних
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.consultant.ru/document/cons_doc_LAW_34683/98ef2900507ab87fe9b12e0457a0b7e8089f7f6b/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-[var(--color-brand)] hover:underline"
                  >
                    ТК РФ, ст. 92 — сокращённое рабочее время
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.consultant.ru/document/cons_doc_LAW_163855/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-[var(--color-brand)] hover:underline"
                  >
                    Договор о ЕАЭС — упрощённый порядок для граждан стран-членов
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <p className="mb-2 text-sm font-semibold">Правовая информация</p>
              <p className="text-xs text-[var(--color-text-secondary)]">
                Информация на сайте не является публичной офертой. Требования к
                гражданству и трудоустройству могут меняться — уточняйте при
                подаче заявки. Для несовершеннолетних (16–17 лет) действуют
                сокращённые нормы рабочего времени согласно ТК РФ.
              </p>
              <a
                href="#"
                className="mt-2 inline-block text-xs text-[var(--color-text-secondary)] hover:text-[var(--color-brand)] hover:underline"
              >
                Политика конфиденциальности
              </a>
            </div>
          </div>

          <div className="mt-6 border-t border-[var(--color-border)] pt-5 text-center text-xs text-[var(--color-text-secondary)] sm:mt-8 sm:pt-6">
            © {year} Сервис набора курьеров. Санкт-Петербург.
          </div>
        </div>
      </footer>

      {/* ─── MODALS ─── */}
      <EbikeModal open={ebikeModal} onClose={() => setEbikeModal(false)} />
      <CalculatorModal open={calcModal} onClose={() => setCalcModal(false)} />
    </div>
  );
}
