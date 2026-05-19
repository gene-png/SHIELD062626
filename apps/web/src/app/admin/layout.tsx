import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";

import { authOptions } from "@/lib/auth/options";
import { PublicFooter } from "@/components/site/PublicFooter";
import { PublicHeader } from "@/components/site/PublicHeader";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect("/sign-in?callbackUrl=/admin/queue");
  }
  if (session.role !== "admin") {
    // Authenticated but wrong role -> 403-equivalent landing. Keep the
    // session intact so the user can navigate elsewhere.
    return (
      <>
        <PublicHeader />
        <main className="mx-auto max-w-3xl px-6 py-16">
          <h1 className="text-2xl font-semibold text-ink-primary">
            Not authorized
          </h1>
          <p className="mt-2 text-ink-secondary">
            Admin views are restricted to Kentro consultants. If you believe you
            should have access, contact your engagement&apos;s Primary POC.
          </p>
        </main>
        <PublicFooter />
      </>
    );
  }
  return (
    <>
      <PublicHeader />
      <main className="mx-auto w-full max-w-6xl px-6 py-10">{children}</main>
      <PublicFooter />
    </>
  );
}
