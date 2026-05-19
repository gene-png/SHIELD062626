/** Wire types for the client-facing /deliverables endpoints. */

export interface ReleasedDeliverable {
  id: string;
  service_id: string;
  service_title: string;
  title: string;
  summary: string | null;
  version: number;
  pdf_artifact_id: string | null;
  xlsx_artifact_id: string | null;
  pdf_filename: string | null;
  xlsx_filename: string | null;
  released_to_client_at: string | null;
}

export interface ReleasedDeliverableList {
  items: ReleasedDeliverable[];
}
