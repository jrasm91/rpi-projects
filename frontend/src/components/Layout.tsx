import { Box, Button, Flex, Heading, SimpleGrid } from '@chakra-ui/react';
import { useEffect, useState } from 'react';

interface LayoutProps {
  children?: any;
}

function now() {
  return { date: new Date().toDateString(), time: new Date().toLocaleTimeString() };
}

export function Layout(props: LayoutProps) {
  const [date, setDate] = useState(now());

  useEffect(() => {
    const timer = setInterval(() => setDate(now()), 1000);

    return function cleanup() {
      clearInterval(timer);
    };
  });

  return (
    <Box bgColor='gray.200'>
      <Flex direction='column'>
        <Flex p='3' boxShadow='md' align='center' justify='space-between' bgColor='blue.900' color='white'>
          <Heading p='1'>Sprinklers</Heading>
          <Flex direction='column' align='flex-end'>
            <Box color='white'>{date.date}</Box>
            <Box color='white'>{date.time}</Box>
          </Flex>
        </Flex>
        <Box flexGrow='2' minHeight='100vh' pb='24'>
          {props.children}
        </Box>
      </Flex>
      <Box boxShadow='md' position={'fixed'} right={0} left={0} bottom={0} z-index={1030} bgColor='blue.900'>
        <SimpleGrid p='2' columns={3} spacing={2}>
          <Button>Zones</Button>
          <Button>History</Button>
          <Button>Sunrise</Button>
        </SimpleGrid>
      </Box>
    </Box>
  );
}
