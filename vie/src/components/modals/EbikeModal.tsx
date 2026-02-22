import { useEffect } from "react";

import { CTAButton } from "../common/CTAButton";
import { Icons } from "../common/Icons";

type EbikeModalProps = {
  open: boolean;
  onClose: () => void;
};

export function EbikeModal({ open, onClose }: EbikeModalProps) {
  useEffect(() => {
    if (open) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4"
      onClick={onClose}
    >
      <div
        className="animate-slide-up relative max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-white p-5 shadow-2xl sm:max-w-lg sm:rounded-2xl sm:p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-gray-300 sm:hidden" />
        <button
          onClick={onClose}
          className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-xl text-[var(--color-text-secondary)] hover:bg-gray-200 hover:text-[var(--color-text)]"
          aria-label="Закрыть"
        >
          &times;
        </button>
        <h3 className="mb-4 text-lg font-bold sm:text-xl">Аренда электровелосипеда</h3>
        <div className="space-y-3 text-sm text-[var(--color-text-secondary)] sm:text-base">
          <p>
            Менеджер подберёт для вас оптимальный вариант аренды электровелосипеда с учетом вашего района
            и графика работы.
          </p>
          <div className="rounded-xl bg-[var(--color-bg-alt)] p-4">
            <p className="font-semibold text-[var(--color-text)]">Условия аренды:</p>
            <ul className="mt-2 space-y-2 text-sm">
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-[var(--color-brand)]">{Icons.check}</span>
                <span>
                  <strong>Средняя стоимость - 5 500 ₽/неделя</strong>
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-[var(--color-brand)]">{Icons.check}</span>
                <span>
                  При более длительной аренде <strong>действуют скидки</strong> - чем дольше арендуете, тем
                  ниже цена за неделю
                </span>
              </li>
            </ul>
            <p className="mt-3 text-xs text-[var(--color-text-secondary)]">
              Точные цены и наличие уточняйте у менеджера
            </p>
          </div>
          <p>
            Электровелосипед позволяет выполнять больше заказов за смену, значительно снижая физическую
            нагрузку и увеличивая ваш доход.
          </p>
        </div>
        <div className="mt-5">
          <CTAButton text="Узнать подробности" className="w-full" />
        </div>
      </div>
    </div>
  );
}
