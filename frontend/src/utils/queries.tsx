import { useQuery } from "@tanstack/react-query";
import { getRequest } from "@/utils/net";

//Example
export const boardsQuery = () => useQuery({
    queryKey: ["textes"],
    queryFn: async () => await getRequest("/textes") as string[]
})