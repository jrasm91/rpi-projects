import { Box, Divider, Heading } from '@chakra-ui/react';
import { ReactNode, useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import io from 'socket.io-client';

interface CardProps {
  children?: ReactNode;
}

function Card({ children }: CardProps) {
  return (
    <Box my='4' p='4' boxShadow='md' bg='white'>
      {children}
    </Box>
  );
}

interface Zone {
  id: string;
  name: string;
  gpio: number;
}

function Dashboard() {
  // const [connected, setConnected] = useState(false);
  const [zones, setZones] = useState<Zone[]>([]);

  // const onMessage = (event: any) => {
  //   const data = JSON.parse(event.data);

  //   console.log(data.type);

  //   switch (data.type) {
  //     case 'connect':
  //       break;
  //     case 'refresh':
  //       break;
  //   }
  // };

  useEffect(() => {
    console.log('connecting');
    const socket = io();
    socket.on('zones', (zones) => {
      console.dir(JSON.parse(zones));
      setZones(JSON.parse(zones));
    });

    return () => {
      console.log('disconnecting');
      socket.disconnect();
    };
  }, []);

  return (
    <Layout>
      <Card>{/* <Heading>Connected: {connected ? 'Yes' : 'No'}</Heading> */}</Card>
      {zones.map((zone) => (
        <Card key={zone.id}>
          <Heading size='lg'>{zone.name}</Heading>
          <Divider my='3'></Divider>
        </Card>
      ))}
    </Layout>
  );
}

export default Dashboard;
