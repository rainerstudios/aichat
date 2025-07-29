import { AnonymousCloudProvider } from "@/components/AnonymousCloudProvider";
import { Thread } from "@/components/assistant-ui/thread";

export default function Home() {
  return (
    <AnonymousCloudProvider>
      <Thread />
    </AnonymousCloudProvider>
  );
}
