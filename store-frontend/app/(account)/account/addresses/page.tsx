import { AddressBook } from "@/components/account/AddressBook";
import { M } from "@/constants/messages";

export default function AddressesPage() {
  return (
    <section className="flex flex-col gap-5">
      <h1 className="text-xl font-black">{M.account.addresses}</h1>
      <AddressBook />
    </section>
  );
}
