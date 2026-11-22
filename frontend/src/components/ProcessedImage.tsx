import { useEffect, useState } from "react";
import { apiGetBlob, apiRequest } from "../api/client";

type Info = {
  version: string;
  original_size: number[];
  processed_size: number[];
  color_mode: string;
  interpolation: string;
  aspect_ratio: string;
  normalization: string;
};

export default function ProcessedImage({ imageId }: { imageId: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [info, setInfo] = useState<Info | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let url: string | null = null;
    setSrc(null);
    setInfo(null);
    setError("");
    Promise.all([
      apiGetBlob(`/images/${imageId}/processed`),
      apiRequest<Info>(`/images/${imageId}/processed/info`),
    ])
      .then(([blob, meta]) => {
        url = URL.createObjectURL(blob);
        setSrc(url);
        setInfo(meta);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Unable to load the preprocessed image."));
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [imageId]);

  return (
    <figure className="mt-6">
      <h5 className="mb-3 text-sm font-semibold text-slate-800">Model input (preprocessed)</h5>
      {error && <p role="alert" className="text-xs text-red-700">{error}</p>}
      {!src && !error && <p className="text-xs text-slate-500">Loading...</p>}
      {src && info && (
        <div className="flex flex-wrap items-start gap-4">
          <img
            src={src}
            alt="Preprocessed model input"
            width={224}
            height={224}
            className="h-56 w-56 rounded border border-slate-200 object-cover"
          />
          <figcaption className="max-w-sm text-xs leading-5 text-slate-600">
            {info.original_size[0]} x {info.original_size[1]} px resized to {info.processed_size[0]} x{" "}
            {info.processed_size[1]} px, {info.color_mode}, {info.interpolation} interpolation, aspect ratio{" "}
            {info.aspect_ratio}. {info.normalization}. Preprocessing version {info.version}. Regenerated from the
            stored original; not stored separately.
          </figcaption>
        </div>
      )}
    </figure>
  );
}
