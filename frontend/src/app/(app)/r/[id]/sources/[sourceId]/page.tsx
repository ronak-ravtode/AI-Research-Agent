import SourceReader from "@/components/SourceReader";

export default async function SourcePage({
  params,
}: {
  params: Promise<{ id: string; sourceId: string }>;
}) {
  const { id, sourceId } = await params;
  return (
    <SourceReader key={`${id}-${sourceId}`} researchId={id} sourceId={sourceId} />
  );
}
