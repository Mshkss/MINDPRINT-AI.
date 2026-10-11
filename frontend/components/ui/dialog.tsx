"use client";
import * as D from "@radix-ui/react-dialog";
import { X } from "lucide-react";
export function Modal({
  open,
  onOpenChange,
  title,
  children,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <D.Root open={open} onOpenChange={onOpenChange}>
      <D.Portal>
        <D.Overlay className="modal-overlay" />
        <D.Content className="modal">
          <div className="row between">
            <D.Title>{title}</D.Title>
            <D.Close className="icon-button" aria-label="Закрыть">
              <X size={20} />
            </D.Close>
          </div>
          <D.Description className="sr-only">{title}</D.Description>
          {children}
        </D.Content>
      </D.Portal>
    </D.Root>
  );
}
