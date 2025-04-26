// app/components/DetailPanel.tsx
import React from 'react';

interface CrackDetails {
  reportId: string;
  location: string;
  type: string;
  length: string;
  width: string;
  inspector?: string;
  inspectionDate?: string;
  treatment?: string;
  status?: string;
}

interface DetailPanelProps {
  details: CrackDetails;
}

const DetailPanel = ({ details }: DetailPanelProps) => {
  return (
    <div className="mt-4">
      <h2 className="text-xl font-bold mb-4">詳細資訊</h2>
      <div className="space-y-2">
        <p>報告編號: {details.reportId}</p>
        <p>位置: {details.location}</p>
        <p>裂縫類型: {details.type}</p>
        <p>裂縫長度: {details.length}</p>
        <p>裂縫深度: {details.width}</p>
        {details.inspector && <p>檢修人員: {details.inspector}</p>}
        {details.inspectionDate && <p>檢修日期: {details.inspectionDate}</p>}
        {details.treatment && <p>處理方式: {details.treatment}</p>}
        {details.status && <p>狀態: {details.status}</p>}
      </div>
    </div>
  );
};

export default DetailPanel;