"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  api,
  type CleanRequest,
  type ContextResponse,
  type ContextUpdate,
  type Profile,
  unwrap,
  uploadCsv,
} from "./client";

/** One place for cache keys, so updates and invalidations always hit the right entry. */
export const queryKeys = {
  health: ["health"] as const,
  samples: ["samples"] as const,
  session: (id: string) => ["session", id] as const,
  info: (id: string) => ["session", id, "info"] as const,
  profile: (id: string) => ["session", id, "profile"] as const,
  context: (id: string) => ["session", id, "context"] as const,
  cleanLog: (id: string) => ["session", id, "clean-log"] as const,
};

const path = (sessionId: string) => ({ params: { path: { session_id: sessionId } } });

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => unwrap(api.GET("/api/health")),
    retry: false,
    refetchInterval: 30_000,
  });
}

export function useSamples() {
  return useQuery({
    queryKey: queryKeys.samples,
    queryFn: () => unwrap(api.GET("/api/samples")),
    staleTime: Infinity, // the list only changes when the server is redeployed
  });
}

export function useStartFromSample() {
  return useMutation({
    mutationFn: (key: string) =>
      unwrap(api.POST("/api/samples/{key}/sessions", { params: { path: { key } } })),
  });
}

export function useUploadCsv() {
  const [progress, setProgress] = useState(0);
  const mutation = useMutation({
    mutationFn: (file: File) => {
      setProgress(0);
      return uploadCsv(file, setProgress);
    },
  });
  return { ...mutation, progress };
}

export function useSessionInfo(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.info(sessionId),
    queryFn: () => unwrap(api.GET("/api/sessions/{session_id}", path(sessionId))),
    staleTime: Infinity, // never changes after upload
  });
}

export function useProfile(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.profile(sessionId),
    queryFn: () => unwrap(api.GET("/api/sessions/{session_id}/profile", path(sessionId))),
  });
}

export function useDataContext(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.context(sessionId),
    queryFn: () => unwrap(api.GET("/api/sessions/{session_id}/context", path(sessionId))),
  });
}

export function useCleanLog(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.cleanLog(sessionId),
    queryFn: () => unwrap(api.GET("/api/sessions/{session_id}/clean/log", path(sessionId))),
  });
}

/** After the data changes, the context may change too (for example, a dropped metric). */
function useRefreshAfterCleaning(sessionId: string) {
  const client = useQueryClient();
  return (profile: Profile) => {
    client.setQueryData(queryKeys.profile(sessionId), profile);
    void client.invalidateQueries({ queryKey: queryKeys.context(sessionId) });
    void client.invalidateQueries({ queryKey: queryKeys.cleanLog(sessionId) });
  };
}

export function useApplyFix(sessionId: string) {
  const refresh = useRefreshAfterCleaning(sessionId);
  return useMutation({
    mutationFn: (fix: CleanRequest) =>
      unwrap(api.POST("/api/sessions/{session_id}/clean", { ...path(sessionId), body: fix })),
    onSuccess: (result) => refresh(result.profile),
  });
}

export function useResetCleaning(sessionId: string) {
  const refresh = useRefreshAfterCleaning(sessionId);
  return useMutation({
    mutationFn: () => unwrap(api.POST("/api/sessions/{session_id}/clean/reset", path(sessionId))),
    onSuccess: refresh,
  });
}

export function useConfirmContext(sessionId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (update: ContextUpdate) =>
      unwrap(api.PUT("/api/sessions/{session_id}/context", { ...path(sessionId), body: update })),
    onSuccess: (response: ContextResponse) => {
      client.setQueryData(queryKeys.context(sessionId), response);
    },
  });
}

export function useDeleteSession() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) =>
      unwrap(api.DELETE("/api/sessions/{session_id}", path(sessionId))),
    onSuccess: (_data, sessionId) => {
      client.removeQueries({ queryKey: queryKeys.session(sessionId) });
    },
  });
}
