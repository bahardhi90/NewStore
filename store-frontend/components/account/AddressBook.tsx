"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { M } from "@/constants/messages";
import { errorMessage } from "@/lib/api/errors";
import { meApi } from "@/lib/api/shop";
import { toFaDigits } from "@/lib/format";
import { toast } from "@/store/uiStore";
import type { Address } from "@/types/api";

import { AddressForm } from "./AddressForm";

const KEY = ["addresses"] as const;

export function AddressBook() {
  const queryClient = useQueryClient();
  const addresses = useQuery({ queryKey: KEY, queryFn: meApi.addresses });
  const [editing, setEditing] = useState<Address | "new" | null>(null);

  const remove = useMutation({
    mutationFn: (id: number) => meApi.deleteAddress(id),
    onSuccess: () => {
      toast.success(M.account.deleted);
      queryClient.invalidateQueries({ queryKey: KEY });
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  if (addresses.isLoading) return <Skeleton className="h-48" />;

  return (
    <div className="flex flex-col gap-4">
      <Button variant="outline" className="w-fit" onClick={() => setEditing("new")}>
        {M.checkout.addAddress}
      </Button>

      {addresses.data?.length === 0 && <EmptyState title={M.checkout.noAddress} />}

      <ul className="grid gap-3 md:grid-cols-2">
        {addresses.data?.map((a) => (
          <li key={a.id} className="rounded-card bg-surface ring-line flex flex-col gap-2 p-5 text-sm ring-1">
            <div className="flex items-center justify-between">
              <span className="font-bold">{a.title}</span>
              {a.is_default && <Badge tone="brand">{M.account.default}</Badge>}
            </div>
            <p className="text-ink-soft leading-7">
              {a.province}، {a.city}، {a.address_line}
            </p>
            <p className="text-muted">
              {a.receiver_name} — <span className="ltr-nums">{toFaDigits(a.receiver_phone)}</span> — کد پستی{" "}
              <span className="ltr-nums">{toFaDigits(a.postal_code)}</span>
            </p>
            <div className="mt-2 flex gap-2">
              <Button size="sm" variant="ghost" onClick={() => setEditing(a)}>
                {M.account.edit}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-sale"
                loading={remove.isPending && remove.variables === a.id}
                onClick={() => {
                  if (window.confirm(M.account.confirmDelete)) remove.mutate(a.id);
                }}
              >
                {M.account.delete}
              </Button>
            </div>
          </li>
        ))}
      </ul>

      <Modal open={editing !== null} onClose={() => setEditing(null)} title={editing === "new" ? M.checkout.addAddress : M.account.edit}>
        <div className="p-5">
          {editing !== null && (
            <AddressForm
              initial={editing === "new" ? null : editing}
              onCancel={() => setEditing(null)}
              onSubmit={async (values) => {
                if (editing === "new") await meApi.createAddress(values);
                else await meApi.updateAddress(editing.id, values);
                await queryClient.invalidateQueries({ queryKey: KEY });
                toast.success(M.account.addressSaved);
                setEditing(null);
              }}
            />
          )}
        </div>
      </Modal>
    </div>
  );
}
