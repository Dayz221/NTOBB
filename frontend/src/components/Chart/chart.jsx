import React from 'react'
import { BarChart } from '@mui/x-charts/BarChart'

import "./chart.css"

const DataBarChart = ({ data, dataKey, label, valueFormatter, colors }) => {
  return (
    <div className="graph__container">
      <BarChart
        dataset={data}
        xAxis={[
          { scaleType: 'band', dataKey: 'time', tickPlacement: "extremities", tickLabelPlacement: "middle"},
        ]}
        yAxis={[
          {
            label: label,
            width: 60,
          },
        ]}
        series={[{ dataKey, label, valueFormatter }]}
        height={300}
        colors={colors}
        borderRadius={5}
      />
    </div>
  )
}

export default DataBarChart