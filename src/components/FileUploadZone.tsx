import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { cn } from "@/lib/utils";

interface FileUploadZoneProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  icon?: React.ReactNode;
  large?: boolean;
}

const FileUploadZone = ({ onFileSelect, accept = "image/*", icon, large = false }: FileUploadZoneProps) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept.split(',').reduce((acc, curr) => ({ ...acc, [curr.trim()]: [] }), {}),
    maxFiles: 1,
    maxSize: 20 * 1024 * 1024, // 20MB
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "border-2 border-dashed rounded-xl transition-smooth cursor-pointer",
        "flex flex-col items-center justify-center text-center",
        "hover:border-primary hover:bg-primary/5",
        isDragActive && "border-primary bg-primary/10",
        large ? "p-12 min-h-[300px]" : "p-8 min-h-[180px]"
      )}
    >
      <input {...getInputProps()} />
      <div className="text-muted-foreground mb-3">
        {icon}
      </div>
      {isDragActive ? (
        <p className="text-sm font-medium text-primary">Drop the file here</p>
      ) : (
        <div>
          <p className="text-sm font-medium mb-1">
            Drag & drop or <span className="text-primary">browse</span>
          </p>
          <p className="text-xs text-muted-foreground">
            Max file size: 20MB
          </p>
        </div>
      )}
    </div>
  );
};

export default FileUploadZone;
