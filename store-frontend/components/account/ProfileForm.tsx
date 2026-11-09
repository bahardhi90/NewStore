"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { M } from "@/constants/messages";
import { SESSION_KEY, useSession } from "@/hooks/useSession";
import { isApiError } from "@/lib/api/errors";
import { meApi } from "@/lib/api/shop";
import { toFaDigits } from "@/lib/format";
import { profileSchema, type ProfileFormValues } from "@/lib/validation";
import { toast } from "@/store/uiStore";
import type { User } from "@/types/api";

export function ProfileForm() {
  const { user, isLoading } = useSession();
  if (isLoading || !user) return <Skeleton className="h-64" />;
  return <ProfileFormInner user={user} />;
}

function ProfileFormInner({ user }: { user: User }) {
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting, isDirty },
    reset,
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { first_name: user.first_name ?? "", last_name: user.last_name ?? "", email: user.email ?? "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      const updated = await meApi.update({ ...values, email: values.email || null });
      queryClient.setQueryData(SESSION_KEY, updated);
      reset({ first_name: updated.first_name ?? "", last_name: updated.last_name ?? "", email: updated.email ?? "" });
      toast.success(M.account.saved);
    } catch (error) {
      if (isApiError(error)) {
        for (const [field, messages] of Object.entries(error.errors)) {
          if (field in values) setError(field as keyof ProfileFormValues, { message: messages[0] });
        }
        toast.error(error.message);
      }
    }
  });

  return (
    <form onSubmit={onSubmit} className="grid max-w-2xl gap-4 sm:grid-cols-2" noValidate>
      <Input label={M.account.firstName} autoComplete="given-name" {...register("first_name")} error={errors.first_name?.message} />
      <Input label={M.account.lastName} autoComplete="family-name" {...register("last_name")} error={errors.last_name?.message} />
      <Input label={M.account.email} type="email" autoComplete="email" ltr {...register("email")} error={errors.email?.message} />
      <Input label={M.account.phone} value={toFaDigits(user.phone)} disabled ltr readOnly />
      <div className="sm:col-span-2">
        <Button type="submit" loading={isSubmitting} disabled={!isDirty}>
          {M.account.save}
        </Button>
      </div>
    </form>
  );
}
