import { BadgeIcon, ClockIcon, PhoneIcon, ReturnIcon, ShieldIcon, TruckIcon } from "@/components/ui/icons";
import { getSiteSettings } from "@/lib/api/catalog";
import { cn } from "@/lib/utils";
import type { TrustBadge } from "@/types/api";

const ICONS: Record<TrustBadge["icon"], typeof BadgeIcon> = {
  return: ReturnIcon,
  truck: TruckIcon,
  shield: ShieldIcon,
  badge: BadgeIcon,
  phone: PhoneIcon,
  clock: ClockIcon,
};

/** Items are managed in admin (site settings). */
export async function TrustBadges({ className, compact = false }: { className?: string; compact?: boolean }) {
  const { trust_badges: items } = await getSiteSettings();
  if (items.length === 0) return null;

  return (
    <ul className={cn("grid grid-cols-2 gap-4 lg:grid-cols-4", className)}>
      {items.map((item, i) => {
        const Icon = ICONS[item.icon] ?? BadgeIcon;
        return (
          <li key={i} className={cn("flex items-center gap-3", !compact && "rounded-card bg-surface ring-line p-4 ring-1")}>
            <span className="bg-sand text-ink flex size-11 shrink-0 items-center justify-center rounded-full">
              <Icon className="size-5" />
            </span>
            <span className="flex flex-col">
              <span className="text-sm font-bold">{item.title}</span>
              {item.subtitle && <span className="text-muted text-xs">{item.subtitle}</span>}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
