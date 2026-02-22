import { useEffect, useState } from "react";

import { CTAButton } from "../common/CTAButton";

type CalculatorModalProps = {
  open: boolean;
  onClose: () => void;
};

export function CalculatorModal({ open, onClose }: CalculatorModalProps) {
  const [hours, setHours] = useState(8);
  const [days, setDays] = useState(6);

  useEffect(() => {
    if (open) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  const rate = 550;
  const perDay = hours * rate;
  const perWeek = perDay * days;
  const perMonth = perWeek * 4;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4"
      onClick={onClose}
    >
      <div
        className="animate-slide-up relative max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-white p-5 shadow-2xl sm:max-w-md sm:rounded-2xl sm:p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-gray-300 sm:hidden" />
        <button
          onClick={onClose}
          className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-xl text-[var(--color-text-secondary)] hover:bg-gray-200"
          aria-label="Закрыть"
        >
          &times;
        </button>

        <h3 className="mb-1 text-lg font-bold sm:text-xl">Калькулятор дохода</h3>
        <p className="mb-5 text-xs text-[var(--color-text-secondary)]">Ставка: 550 ₽/час</p>

        <div className="mb-5">
          <div className="mb-2 flex items-center justify-between">
            <label className="text-sm font-medium">Часы в день</label>
            <span className="rounded-lg bg-[var(--color-brand)]/10 px-2.5 py-1 text-sm font-bold text-[var(--color-brand)]">
              {hours} ч
            </span>
          </div>
          <input
            type="range"
            min={4}
            max={16}
            step={1}
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            className="w-full"
          />
          <div className="mt-1 flex justify-between text-[10px] text-[var(--color-text-secondary)]">
            <span>4 ч</span>
            <span>16 ч</span>
          </div>
        </div>

        <div className="mb-6">
          <label className="mb-2 block text-sm font-medium">Дней в неделю</label>
          <div className="flex gap-1.5">
            {[1, 2, 3, 4, 5, 6, 7].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`flex h-10 w-10 items-center justify-center rounded-lg text-sm font-semibold transition-all ${
                  days === d
                    ? "bg-[var(--color-brand)] text-white shadow-md"
                    : "bg-[var(--color-bg-alt)] text-[var(--color-text)] hover:bg-[var(--color-brand-light)]"
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 rounded-xl bg-[var(--color-bg-alt)] p-4">
          <div className="text-center">
            <p className="text-[10px] text-[var(--color-text-secondary)] sm:text-xs">В день</p>
            <p className="text-base font-extrabold text-[var(--color-text)] sm:text-lg">
              {perDay.toLocaleString("ru-RU")}&nbsp;₽
            </p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-[var(--color-text-secondary)] sm:text-xs">В неделю</p>
            <p className="text-base font-extrabold text-[var(--color-text)] sm:text-lg">
              {perWeek.toLocaleString("ru-RU")}&nbsp;₽
            </p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-[var(--color-text-secondary)] sm:text-xs">В месяц</p>
            <p className="text-base font-extrabold text-[var(--color-brand)] sm:text-lg">
              {perMonth.toLocaleString("ru-RU")}&nbsp;₽
            </p>
          </div>
        </div>

        <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-center">
          <p className="text-xs text-amber-700">
            🎁 <strong>+ стартовый бонус 10 000-15 000 ₽</strong>
          </p>
        </div>

        <p className="mt-3 text-center text-[10px] text-[var(--color-text-secondary)]">
          Без учета чаевых и дополнительных выплат
        </p>

        <div className="mt-4">
          <CTAButton text="Начать зарабатывать" className="w-full" />
        </div>
      </div>
    </div>
  );
}
