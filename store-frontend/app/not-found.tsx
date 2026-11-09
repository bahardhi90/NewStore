import { ButtonLink } from "@/components/ui/Button";
import { M } from "@/constants/messages";

export default function NotFound() {
  return (
    <div className="container-page flex flex-col items-center gap-4 py-24 text-center">
      <p className="text-line text-6xl font-black">۴۰۴</p>
      <h1 className="text-2xl font-bold">{M.errors.notFoundTitle}</h1>
      <p className="text-muted">{M.errors.notFoundText}</p>
      <ButtonLink href="/">{M.payment.backHome}</ButtonLink>
    </div>
  );
}
