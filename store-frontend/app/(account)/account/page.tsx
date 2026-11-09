import { ProfileForm } from "@/components/account/ProfileForm";
import { M } from "@/constants/messages";

export default function ProfilePage() {
  return (
    <section className="rounded-card bg-surface ring-line p-6 ring-1">
      <h1 className="mb-6 text-xl font-black">{M.account.profile}</h1>
      <ProfileForm />
    </section>
  );
}
