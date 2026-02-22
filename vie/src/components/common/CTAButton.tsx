import { getBotLink } from "../../config";
import { COPY } from "../../content/copy";
import { Icons } from "./Icons";

type CTAButtonProps = {
  text?: string;
  secondary?: boolean;
  href?: string;
  className?: string;
};

export function CTAButton({
  text = COPY.ctaDefault,
  secondary = false,
  href,
  className = "",
}: CTAButtonProps) {
  const link = href || getBotLink();

  if (secondary) {
    return (
      <a
        href={link}
        target="_blank"
        rel="noopener noreferrer"
        className={`inline-flex items-center justify-center gap-2 rounded-xl border-2 border-[var(--color-brand)] px-5 py-3 text-base font-semibold text-[var(--color-brand)] transition-all duration-200 hover:bg-[var(--color-brand-light)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)] focus:ring-offset-2 active:scale-[0.97] sm:px-6 sm:py-3.5 ${className}`}
      >
        {Icons.telegram}
        <span>{text}</span>
      </a>
    );
  }

  return (
    <a
      href={link}
      target="_blank"
      rel="noopener noreferrer"
      className={`btn-pulse inline-flex items-center justify-center gap-2.5 rounded-xl bg-[var(--color-brand)] px-6 py-3.5 text-base font-bold text-white shadow-lg shadow-[var(--color-brand)]/25 transition-all duration-200 hover:bg-[var(--color-brand-dark)] hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)] focus:ring-offset-2 active:scale-[0.97] sm:px-8 sm:py-4 sm:text-lg ${className}`}
    >
      {Icons.telegram}
      <span>{text}</span>
    </a>
  );
}
