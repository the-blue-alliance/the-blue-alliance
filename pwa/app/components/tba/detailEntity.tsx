interface DetailEntityProps {
  icon: React.ReactNode;
  children?: React.ReactNode;
}

export default function DetailEntity({ icon, children }: DetailEntityProps) {
  return (
    <div className="flex items-center gap-2 [&>svg]:size-4">
      {icon}
      <p className="font-medium">{children}</p>
    </div>
  );
}
