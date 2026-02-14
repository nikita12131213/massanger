export type User = { id: number; username: string };
export type Attachment = { id: number; url: string; kind: string; mime: string; size: number };
export type Message = {
  id: number;
  conversation_id: number;
  sender_id: number;
  text: string;
  created_at: string;
  edited_at?: string | null;
  attachments: Attachment[];
  temp_id?: string;
  pending?: boolean;
};
export type Conversation = {
  id: number;
  peer: User | null;
  last_message?: Message | null;
  unread_count: number;
};