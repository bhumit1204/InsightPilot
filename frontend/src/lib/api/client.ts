/**
 * Typed access to the InsightPilot backend.
 *
 * Types come from `schema.ts`, which is generated from the backend's OpenAPI schema
 * (`npm run api:types`), so a renamed field in Python becomes a type error here.
 */
import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

type Schemas = components["schemas"];
export type SessionCreated = Schemas["SessionCreated"];
export type SessionInfo = Schemas["SessionInfo"];
export type SampleDataset = Schemas["SampleDataset"];
export type Profile = Schemas["Profile"];
export type ColumnProfile = Schemas["ColumnProfile"];
export type QualityWarning = Schemas["QualityWarning"];
export type CleanRequest = Schemas["CleanRequest"];
export type CleanResult = Schemas["CleanResult"];
export type CleanLog = Schemas["CleanLog"];
export type DataContext = Schemas["DataContext"];
export type ContextOptions = Schemas["ContextOptions"];
export type ContextResponse = Schemas["ContextResponse"];
export type ContextUpdate = Schemas["ContextUpdate"];

/** Must match MAX_UPLOAD_MB on the backend; checked here first so people wait less. */
export const MAX_UPLOAD_MB = 50;

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

export const api = createClient<paths>({ baseUrl: API_URL });

/** Every failure, from the server or the network, is raised as one of these. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: unknown;

  constructor(code: string, message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }

  /** 4xx errors mean the request itself was wrong, so retrying will not help. */
  get isClientError() {
    return this.status >= 400 && this.status < 500;
  }
}

type ErrorShape = { error?: { code?: string; message?: string; details?: unknown } };

function fromBody(body: unknown, status: number): ApiError {
  const error = (body as ErrorShape | undefined)?.error;
  if (error?.code && error.message) {
    return new ApiError(error.code, error.message, status, error.details);
  }
  return new ApiError("HTTP_ERROR", `The server answered with status ${status}.`, status);
}

function networkError(): ApiError {
  return new ApiError(
    "NETWORK_ERROR",
    `Can't reach the InsightPilot server at ${API_URL}. Check that the backend is running.`,
    0,
  );
}

type FetchResult<T> = { data?: T; error?: unknown; response: Response };

/** Turn an openapi-fetch result into data, or throw an ApiError. */
export async function unwrap<T>(request: Promise<FetchResult<T>>): Promise<T> {
  let result: FetchResult<T>;
  try {
    result = await request;
  } catch {
    throw networkError();
  }
  if (result.error !== undefined || !result.response.ok) {
    throw fromBody(result.error, result.response.status);
  }
  return result.data as T;
}

/**
 * Upload a CSV with progress updates (fetch cannot report upload progress, XHR can).
 * `onProgress` receives a number from 0 to 1.
 */
export function uploadCsv(
  file: File,
  onProgress?: (fraction: number) => void,
  signal?: AbortSignal,
): Promise<SessionCreated> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_URL}/api/sessions`);
    xhr.responseType = "json";

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(event.loaded / event.total);
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress?.(1);
        resolve(xhr.response as SessionCreated);
      } else {
        reject(fromBody(xhr.response, xhr.status));
      }
    };
    xhr.onerror = () => reject(networkError());
    xhr.onabort = () => reject(new ApiError("ABORTED", "Upload cancelled.", 0));

    signal?.addEventListener("abort", () => xhr.abort(), { once: true });

    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}
