import ResearchRun from "@/components/ResearchRun";

export default async function ResearchPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ResearchRun key={id} id={id} />;
}
