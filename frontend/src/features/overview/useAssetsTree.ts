"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchAssetsTree } from "@/lib/api/assets";
import { queryKeys } from "@/lib/api/query-keys";
import type { AssetsTreeResponse } from "@/lib/api/types";

import { rollupTree } from "./treeUtils";

export type UseAssetsTreeResult = {
  tree: AssetsTreeResponse | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  refetch: () => void;
};

export function useAssetsTree(): UseAssetsTreeResult {
  const query = useQuery({
    queryKey: queryKeys.assetsTree,
    queryFn: async ({ signal }) => {
      const result = await fetchAssetsTree(signal);
      return {
        ...result.data,
        root: rollupTree(result.data.root),
      };
    },
    staleTime: 60_000,
    retry: false,
  });

  return {
    tree: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: () => {
      void query.refetch();
    },
  };
}
